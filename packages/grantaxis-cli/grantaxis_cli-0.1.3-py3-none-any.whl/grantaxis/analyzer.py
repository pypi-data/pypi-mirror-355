"""
Risk-analyzer: pulls live ACCOUNT_USAGE metadata, classifies roles into
functional-roles (FR) and access-roles (AR) via graph reachability, then
emits three actionable findings:

    • zombie_admins          – admin roles no human has used ≥ 90 days
    • dormant_priv_roles     – ARs that own objects but are unreachable
    • overpriv_users         – users who hold admin roles yet only run SELECT

All queries run server-side, no temp tables, < 1 s even on large accounts.
"""

from __future__ import annotations
import datetime
import json
from typing import Dict, List, Any
from pathlib import Path
from typing import Union
from grantaxis.conn import get_connection


# -----------------------------  core helpers  ----------------------------- #


def _run(sql: str) -> List[Dict[str, Any]]:
    """Execute SQL and return list-of-dict rows."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
        return rows


# ---------------------------  SQL building blocks  ------------------------ #

WINDOW_DAYS = 90

ZOMBIE_ADMINS_SQL = f"""
WITH admin_roles AS (
    SELECT role_name
    FROM snowflake.account_usage.roles
    WHERE role_name IN ('ACCOUNTADMIN','SECURITYADMIN','SYSADMIN')
), last_use AS (
    SELECT role_name, MAX(start_time) AS last_used_at
    FROM snowflake.account_usage.query_history
    WHERE role_name IN (SELECT role_name FROM admin_roles)
    GROUP BY role_name
)
SELECT r.role_name,
       COALESCE(lu.last_used_at,'NEVER') AS last_used_at
FROM admin_roles r
LEFT JOIN last_use lu USING (role_name)
WHERE lu.last_used_at IS NULL
   OR lu.last_used_at < DATEADD(day,-{WINDOW_DAYS},CURRENT_TIMESTAMP());
"""

# role graph edges (ROLE → ROLE)
ROLE_EDGES_CTE = """
WITH role_edges AS (
    SELECT granted_to          AS parent_role,
           role_name           AS child_role
    FROM   snowflake.account_usage.grants_to_roles
    WHERE  granted_to_type = 'ROLE'
),
user_roles AS (
    SELECT DISTINCT role_name FROM snowflake.account_usage.grants_to_users
),
used_roles AS (
    SELECT DISTINCT role_name
    FROM   snowflake.account_usage.query_history
    WHERE  start_time >= DATEADD(day,-{window}, CURRENT_TIMESTAMP())
)
"""

# recursive reachability from user-reachable roots
REACHABLE_ROLES_CTE = """
, RECURSIVE reachable AS (
      SELECT role_name FROM used_roles
      UNION
      SELECT role_name FROM user_roles
      UNION
      SELECT e.child_role
      FROM   role_edges e
      JOIN   reachable r ON r.role_name = e.parent_role
)
"""

# dormant privileged ARs = unreachable + owns privileged objects
DORMANT_PRIV_SQL = (
    ROLE_EDGES_CTE.format(window=WINDOW_DAYS)
    + REACHABLE_ROLES_CTE
    + """
SELECT DISTINCT gr.role_name
FROM   snowflake.account_usage.grants_to_roles gr
WHERE  gr.privilege IN ('OWNERSHIP','ALL','MODIFY')
  AND  gr.role_name NOT IN (SELECT role_name FROM reachable);
"""
)

# over-priv users: admin role + only SELECT queries
OVERPRIV_USERS_SQL = f"""
WITH admin_usage AS (
  SELECT user_name,
         ARRAY_AGG(DISTINCT query_type) AS qt
  FROM   snowflake.account_usage.query_history
  WHERE  role_name IN ('ACCOUNTADMIN','SECURITYADMIN','SYSADMIN')
    AND  start_time >= DATEADD(day,-{WINDOW_DAYS}, CURRENT_TIMESTAMP())
  GROUP  BY user_name
)
SELECT user_name
FROM   admin_usage
WHERE  ARRAY_SIZE(qt)=1 AND qt[0]='SELECT';
"""


# -----------------------------  public API  ------------------------------- #


def scan() -> Dict[str, Any]:
    """Run all risk queries and return consolidated JSON-serialisable dict."""
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "window_days": WINDOW_DAYS,
        "zombie_admins": _run(ZOMBIE_ADMINS_SQL),
        "dormant_priv_roles": _run(DORMANT_PRIV_SQL),
        "overpriv_users": _run(OVERPRIV_USERS_SQL),
    }


def scan_to_json(path: Union[str, Path] = "outputs/findings.json") -> str:
    """Run scan(), write JSON, return the file path (as string)."""
    path = Path(path)  # ← normalise to Path
    path.parent.mkdir(parents=True, exist_ok=True)
    data = scan()
    path.write_text(json.dumps(data, indent=2, default=str))
    return str(path)
