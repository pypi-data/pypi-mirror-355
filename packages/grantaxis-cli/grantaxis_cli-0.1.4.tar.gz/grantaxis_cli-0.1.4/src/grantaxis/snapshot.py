from __future__ import annotations
import logging
import os
import time
from collections import OrderedDict, defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Sequence, Set, Optional

import snowflake.connector
import yaml
import re

"""
GrantAxis – Enhanced RBAC Snapshot Tool
======================================
**Comprehensive Snowflake RBAC analysis with role hierarchy mapping**

Key Features:
* Proper column mapping for all three account usage views
* Role hierarchy detection and classification
* Functional vs Access role identification
* Object-level permission tracking
* Future grants analysis
* Account-level privilege tracking
"""

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LVL = os.getenv("GRANTAXIS_LOG_LEVEL", "INFO").upper()
logging.basicConfig(format="[%(asctime)s] %(levelname)s – %(message)s", level=LOG_LVL)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & config
# ---------------------------------------------------------------------------
ACCOUNT_USAGE = "SNOWFLAKE.ACCOUNT_USAGE"
REQUIRED_VIEWS: Sequence[str] = (
    f"{ACCOUNT_USAGE}.GRANTS_TO_ROLES",
    f"{ACCOUNT_USAGE}.GRANTS_TO_USERS",
    f"{ACCOUNT_USAGE}.USERS",
)

STMT_TIMEOUT_SEC = int(os.getenv("GRANTAXIS_STMT_TIMEOUT_SEC", "30"))
MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 2.5

SYSTEM_ROLES = {
    "ACCOUNTADMIN",
    "SYSADMIN",
    "SECURITYADMIN",
    "USERADMIN",
    "PUBLIC",
    "ORGADMIN",
    "SNOWFLAKE_LEARNING_ROLE",
}
INTERNAL_SCHEMAS = {"INFORMATION_SCHEMA", "SNOWFLAKE", "SNOWFLAKE_SAMPLE_DATA"}


# Role classification patterns
FUNCTIONAL_ROLE_PATTERNS = [
    "_USER",
    "_HUMAN",
    "_PERSON",
    "ANALYST",
    "DEVELOPER",
    "ADMIN",
]
ACCESS_ROLE_PATTERNS = ["_READ", "_WRITE", "_ACCESS", "_ROLE", "_PRIVS"]

GUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class SnapshotError(Exception):
    """Top level failure for snapshot compilation."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GrantFact:
    """Unified grant representation across all sources"""

    database_name: str
    schema_name: str
    object_type: str
    object_name: str
    privilege: str
    grantee_type: str  # ROLE or USER
    grantee_name: str
    with_grant_option: bool
    source: str  # DIRECT_OBJECT | ROLE_HIERARCHY | FUTURE | ACCOUNT
    granted_by: Optional[str] = None
    created_on: Optional[str] = None

    def hash_id(self) -> str:
        """Generate deterministic unique identifier"""
        key = "|".join(
            [
                self.database_name,
                self.schema_name,
                self.object_type,
                self.object_name,
                self.privilege,
                self.grantee_type,
                self.grantee_name,
                "1" if self.with_grant_option else "0",
                self.source,
            ]
        )
        return sha256(key.encode()).hexdigest()

    def to_record(self) -> Dict[str, Any]:
        rec = OrderedDict(asdict(self))
        rec["id"] = self.hash_id()

        # Convert datetime objects to ISO strings for YAML serialization
        if rec.get("created_on") is not None and hasattr(
            rec["created_on"], "isoformat"
        ):
            rec["created_on"] = rec["created_on"].isoformat()

        return rec


@dataclass
class RoleInfo:
    """Role classification and hierarchy information"""

    name: str
    role_type: str  # FUNCTIONAL | ACCESS | SYSTEM | CUSTOM
    granted_to_users: Set[str]
    granted_to_roles: Set[str]
    has_object_privileges: bool
    is_leaf_role: bool  # True if only granted to users, not other roles
    hierarchy_level: int = 0


@dataclass
class UserInfo:
    """User information from USERS view"""

    name: str
    login_name: str
    display_name: Optional[str]
    email: Optional[str]
    disabled: bool
    default_role: Optional[str]
    created_on: Optional[str]
    last_success_login: Optional[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _bool(val: Any) -> bool:
    """Convert various boolean representations to bool"""
    if val is None:
        return False
    return str(val).upper() in {"TRUE", "YES", "Y", "1"}


def _safe_get(row: Dict[str, Any], *keys: str) -> str:
    """Safely get value from row, trying multiple keys, returning empty string if none found"""
    for key in keys:
        val = row.get(key)
        if val is not None:
            return str(val)
    return ""


def _run_query(
    ctx: snowflake.connector.SnowflakeConnection, sql: str
) -> List[Dict[str, Any]]:
    """Execute SQL with retry; return list[dict] rows."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with ctx.cursor() as cur:
                cur.execute(sql)
                cols = [d[0].lower() for d in cur.description]
                return [dict(zip(cols, row)) for row in cur]
        except snowflake.connector.errors.Error as exc:
            log.warning("Query failed (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
            if attempt >= MAX_RETRIES:
                raise SnapshotError("SQL execution repeatedly failed") from exc
            time.sleep(RETRY_BACKOFF_SEC * attempt)
    return []


def _assert_permissions(ctx) -> None:
    """Verify access to required views"""
    for view in REQUIRED_VIEWS:
        try:
            _run_query(ctx, f"SELECT 1 FROM {view} LIMIT 1")
        except SnapshotError:
            log.warning(f"Skipping missing or unauthorized view: {view}")


# ---------------------------------------------------------------------------
# Role Analysis
# ---------------------------------------------------------------------------
def _classify_role(role_name: str, role_info: RoleInfo) -> str:
    """Classify role based on name patterns and usage"""
    name_upper = role_name.upper()

    # System roles first
    if name_upper in [
        "ACCOUNTADMIN",
        "SECURITYADMIN",
        "USERADMIN",
        "SYSADMIN",
        "PUBLIC",
    ]:
        return "SYSTEM"

    # Functional roles (typically granted to users)
    if any(pattern in name_upper for pattern in FUNCTIONAL_ROLE_PATTERNS) or (
        role_info.granted_to_users and not role_info.granted_to_roles
    ):
        return "FUNCTIONAL"

    # Access roles (typically granted to other roles)
    if any(pattern in name_upper for pattern in ACCESS_ROLE_PATTERNS) or (
        role_info.granted_to_roles
        and not role_info.granted_to_users
        and role_info.has_object_privileges
    ):
        return "ACCESS"

    return "CUSTOM"


def _build_role_hierarchy(role_grants: List[GrantFact]) -> Dict[str, RoleInfo]:
    """Build role hierarchy and classification"""
    roles = defaultdict(
        lambda: RoleInfo(
            name="",
            role_type="",
            granted_to_users=set(),
            granted_to_roles=set(),
            has_object_privileges=False,
            is_leaf_role=True,
        )
    )

    # First pass: collect role grant relationships
    for grant in role_grants:
        if grant.object_type == "ROLE" and grant.grantee_type == "ROLE":
            # Role granted to role
            role_name = grant.object_name
            grantee_role = grant.grantee_name

            if role_name not in roles:
                roles[role_name].name = role_name
            if grantee_role not in roles:
                roles[grantee_role].name = grantee_role

            roles[role_name].granted_to_roles.add(grantee_role)
            roles[grantee_role].is_leaf_role = False

        elif grant.object_type == "ROLE" and grant.grantee_type == "USER":
            # Role granted to user
            role_name = grant.object_name
            user_name = grant.grantee_name

            if role_name not in roles:
                roles[role_name].name = role_name
            roles[role_name].granted_to_users.add(user_name)

    # Second pass: identify roles with object privileges
    object_grants = [g for g in role_grants if g.object_type != "ROLE"]
    for grant in object_grants:
        if grant.grantee_type == "ROLE":
            role_name = grant.grantee_name
            if role_name not in roles:
                roles[role_name].name = role_name
            roles[role_name].has_object_privileges = True

    # Third pass: classify roles
    for role_name, role_info in roles.items():
        role_info.role_type = _classify_role(role_name, role_info)

    return dict(roles)


# ---------------------------------------------------------------------------
# Data Fetchers
# ---------------------------------------------------------------------------
def _fetch_users(ctx) -> Dict[str, UserInfo]:
    """Fetch user information from USERS view"""
    sql = f"""
        SELECT name, login_name, display_name, email, disabled, 
               default_role, created_on, last_success_login
        FROM {ACCOUNT_USAGE}.USERS 
        WHERE deleted_on IS NULL
    """

    users = {}
    try:
        for row in _run_query(ctx, sql):
            # Convert datetime fields to strings
            created_on = row.get("created_on")
            if created_on and hasattr(created_on, "isoformat"):
                created_on = created_on.isoformat()

            last_success_login = row.get("last_success_login")
            if last_success_login and hasattr(last_success_login, "isoformat"):
                last_success_login = last_success_login.isoformat()

            user = UserInfo(
                name=_safe_get(row, "name"),
                login_name=_safe_get(row, "login_name"),
                display_name=row.get("display_name"),
                email=row.get("email"),
                disabled=_bool(row.get("disabled")),
                default_role=row.get("default_role"),
                created_on=created_on,
                last_success_login=last_success_login,
            )
            users[user.name] = user
    except Exception as e:
        log.warning(f"Failed to fetch users: {e}")

    return users


def _fetch_role_grants(ctx) -> Iterable[GrantFact]:
    """Fetch role grants from GRANTS_TO_USERS view"""
    sql = f"""
        SELECT created_on, role, granted_to, grantee_name, granted_by
        FROM {ACCOUNT_USAGE}.GRANTS_TO_USERS 
        WHERE deleted_on IS NULL
    """

    for row in _run_query(ctx, sql):
        # Convert datetime to string
        created_on = row.get("created_on")
        if created_on and hasattr(created_on, "isoformat"):
            created_on = created_on.isoformat()

        yield GrantFact(
            database_name="",
            schema_name="",
            object_type="ROLE",
            object_name=_safe_get(row, "role"),
            privilege="USAGE",  # Role usage privilege
            grantee_type=_safe_get(row, "granted_to", "grantee_type"),
            grantee_name=_safe_get(row, "grantee_name"),
            with_grant_option=False,  # Role grants don't have grant option
            source="ROLE_HIERARCHY",
            granted_by=row.get("granted_by"),
            created_on=created_on,
        )


def _fetch_object_grants(ctx) -> Iterable[GrantFact]:
    """Fetch object grants from GRANTS_TO_ROLES view"""
    sql = f"""
        SELECT created_on, privilege, granted_on, name, table_catalog, 
               table_schema, granted_to, grantee_name, grant_option, granted_by
        FROM {ACCOUNT_USAGE}.GRANTS_TO_ROLES 
        WHERE deleted_on IS NULL
    """

    for row in _run_query(ctx, sql):
        # Handle the different column names properly
        object_type = _safe_get(row, "granted_on", "object_type")
        object_name = _safe_get(row, "name", "object_name")
        database_name = _safe_get(row, "table_catalog", "database_name")
        schema_name = _safe_get(row, "table_schema", "schema_name")

        # Convert datetime to string
        created_on = row.get("created_on")
        if created_on and hasattr(created_on, "isoformat"):
            created_on = created_on.isoformat()

        yield GrantFact(
            database_name=database_name,
            schema_name=schema_name,
            object_type=object_type,
            object_name=object_name,
            privilege=_safe_get(row, "privilege"),
            grantee_type=_safe_get(row, "granted_to", "grantee_type"),
            grantee_name=_safe_get(row, "grantee_name"),
            with_grant_option=_bool(
                row.get("grant_option", row.get("with_grant_option"))
            ),
            source="DIRECT_OBJECT",
            granted_by=row.get("granted_by"),
            created_on=created_on,
        )


def _fetch_future_grants(ctx) -> Iterable[GrantFact]:
    """Fetch future grants"""
    try:
        dbs = _run_query(ctx, "SHOW DATABASES")
        for db in dbs:
            name = db["name"]
            try:
                rows = _run_query(ctx, f"SHOW FUTURE GRANTS IN DATABASE {name}")
                for row in rows:
                    yield GrantFact(
                        database_name=_safe_get(row, "database_name") or name,
                        schema_name=_safe_get(row, "schema_name"),
                        object_type=_safe_get(row, "grant_on", "object_type"),
                        object_name="<FUTURE>",
                        privilege=_safe_get(row, "privilege"),
                        grantee_type=_safe_get(row, "granted_to", "grantee_type"),
                        grantee_name=_safe_get(row, "grantee_name"),
                        with_grant_option=_bool(
                            row.get("grant_option", row.get("with_grant_option"))
                        ),
                        source="FUTURE",
                    )
            except Exception as e:
                log.warning(f"Skipping FUTURE GRANTS in {name}: {e}")
    except Exception as e:
        log.warning(f"Unable to query SHOW FUTURE GRANTS: {e}")


def _fetch_account_grants(ctx) -> Iterable[GrantFact]:
    """Fetch account-level grants"""
    try:
        rows = _run_query(ctx, "SHOW GRANTS ON ACCOUNT")
        for row in rows:
            yield GrantFact(
                database_name="",
                schema_name="",
                object_type="ACCOUNT",
                object_name="ACCOUNT",
                privilege=_safe_get(row, "privilege"),
                grantee_type=_safe_get(row, "granted_to", "grantee_type"),
                grantee_name=_safe_get(row, "grantee_name"),
                with_grant_option=_bool(
                    row.get("grant_option", row.get("with_grant_option"))
                ),
                source="ACCOUNT",
            )
    except Exception as e:
        log.warning(f"Unable to query SHOW GRANTS ON ACCOUNT: {e}")


# ---------------------------------------------------------------------------
# Main Snapshot API
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Main Snapshot API
# ---------------------------------------------------------------------------
def compile_snapshot(ctx: snowflake.connector.SnowflakeConnection) -> Dict[str, Any]:
    """Compile comprehensive RBAC snapshot"""
    log.info("Starting comprehensive RBAC snapshot...")
    # Set session timeout
    with ctx.cursor() as cur:
        cur.execute(
            f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS={STMT_TIMEOUT_SEC}"
        )
    _assert_permissions(ctx)
    # Fetch all data
    log.info("Fetching users...")
    users = _fetch_users(ctx)
    log.info("Fetching grants...")
    all_grants = []
    # Collect all grants
    for fetcher in [
        _fetch_role_grants,
        _fetch_object_grants,
        _fetch_future_grants,
        _fetch_account_grants,
    ]:
        grants = list(fetcher(ctx))
        all_grants.extend(grants)
        log.debug(f"Fetched {len(grants)} grants from {fetcher.__name__}")
    # Build role hierarchy
    log.info("Analyzing role hierarchy...")
    role_hierarchy = _build_role_hierarchy(all_grants)

    # Filter out system roles from role hierarchy before counting
    filtered_role_hierarchy = {
        name: role
        for name, role in role_hierarchy.items()
        if role.role_type != "SYSTEM"
    }

    # Filter out service users and disabled users
    filtered_users = {
        name: user
        for name, user in users.items()
        if not (
            # drop disabled users
            user.disabled
            # drop GUID-style service principals
            or GUID_RE.match(name)
            # drop other known service accounts
            or name.upper().startswith("SNOWFLAKE_SERVICE")
        )
    }

    # Compile results and sort by ID (CRITICAL FIX)
    # 🎯 Filter and normalize
    records = []
    default_role_info = RoleInfo(
        name="",
        role_type="",
        granted_to_users=set(),
        granted_to_roles=set(),
        has_object_privileges=False,
        is_leaf_role=True,
    )
    for g in all_grants:
        # ❌ Skip noise and internal objects
        if (
            g.grantee_type == "APPLICATION_ROLE"
            or g.source == "ACCOUNT"
            or g.grantee_name in SYSTEM_ROLES
            or (g.database_name or "").upper() == "SNOWFLAKE"
            or g.object_type in INTERNAL_SCHEMAS
        ):
            continue

        # ❌ Skip non-leaf roles from hierarchy ONLY for non-role grants
        # Keep role-to-role grants (like "grant usage on role AAA to role BBB")
        if (
            g.source == "ROLE_HIERARCHY"
            and g.grantee_type == "ROLE"
            and g.object_type != "ROLE"
        ):
            role_info = role_hierarchy.get(g.grantee_name, default_role_info)
            if not role_info.is_leaf_role:
                continue

        # ✅ Passed all filters
        records.append(g.to_record())
    records.sort(key=lambda r: r["id"])  # Sort by the hash ID, not other fields
    log.debug(f"Sorted {len(records)} records by ID")

    # Create summary statistics using filtered data
    stats = {
        "total_grants": len(records),
        "total_users": len(filtered_users),  # Use filtered users (excluding disabled)
        "total_roles": len(
            filtered_role_hierarchy
        ),  # Use filtered roles (excluding system)
        "functional_roles": len(
            [r for r in filtered_role_hierarchy.values() if r.role_type == "FUNCTIONAL"]
        ),
        "access_roles": len(
            [r for r in filtered_role_hierarchy.values() if r.role_type == "ACCESS"]
        ),
        "system_roles": len(
            [
                r for r in role_hierarchy.values() if r.role_type == "SYSTEM"
            ]  # Keep original for system count
        ),
        "grants_by_source": {
            source: len([r for r in records if r["source"] == source])
            for source in ["DIRECT_OBJECT", "ROLE_HIERARCHY", "FUTURE", "ACCOUNT"]
        },
    }
    log.info(
        f"Snapshot complete - {stats['total_grants']} grants,"
        f"{stats['total_users']} users, {stats['total_roles']} roles"
    )
    return {
        "snapshot_metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "statistics": stats,
        },
        "users": {
            name: asdict(user) for name, user in filtered_users.items()
        },  # Use filtered users
        "roles": {
            name: asdict(role) for name, role in filtered_role_hierarchy.items()
        },  # Use filtered roles
        "grants": records,
    }


def write_baseline(snapshot: Dict[str, Any], outfile: str | os.PathLike) -> None:
    """Write comprehensive baseline to YAML"""
    # Generate snapshot ID based on all grants
    snapshot_id = sha256(
        "".join(g["id"] for g in snapshot["grants"]).encode()
    ).hexdigest()

    output = OrderedDict(
        [
            ("snapshot_id", snapshot_id),
            ("metadata", snapshot["snapshot_metadata"]),
            ("users", snapshot["users"]),
            ("roles", snapshot["roles"]),
            ("grants", snapshot["grants"]),
        ]
    )

    with open(outfile, "w", encoding="utf-8") as fh:
        yaml.safe_dump(output, fh, sort_keys=False, default_flow_style=False)

    log.info(f"Comprehensive baseline written → {outfile}")


# ---------------------------------------------------------------------------
# Debug entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    from pathlib import Path

    creds_json = os.getenv("SNOWFLAKE_CREDS_JSON")
    if not creds_json:
        raise SystemExit("Set SNOWFLAKE_CREDS_JSON env var with connector kwargs!")

    creds = json.loads(creds_json)
    with snowflake.connector.connect(**creds) as con:
        snapshot = compile_snapshot(con)
        write_baseline(snapshot, Path("rbac_baseline.yaml"))

        # Print summary
        stats = snapshot["snapshot_metadata"]["statistics"]
        print("✔ RBAC baseline generated:")
        print(f"  • {stats['total_grants']} total grants")
        print(f"  • {stats['total_users']} users")
        print(
            f"  • {stats['total_roles']} roles ({stats['functional_roles']}"
            f"functional, {stats['access_roles']} access)"
        )
        print(f"  • Grants by source: {stats['grants_by_source']}")
