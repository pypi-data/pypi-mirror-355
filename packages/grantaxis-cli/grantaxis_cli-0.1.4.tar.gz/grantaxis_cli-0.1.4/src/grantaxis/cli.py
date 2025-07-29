from __future__ import annotations
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import click
import yaml
import getpass
from textwrap import dedent
from grantaxis.baseline import dump_baseline, load_baseline
from grantaxis.config import Config, ConfigError
from grantaxis.diff import diff_records, render_markdown

"""
GrantAxis – cli.py
==================
Single entry‑point CLI using **Click**.

Supported sub‑commands (MVP)
---------------------------
* `grantaxis init`    – snapshot live account ➜ baseline YAML.
* `grantaxis diff`    – compare baseline vs. snapshot file (or live).

Typical flows
-------------
```bash
# 1. snapshot current prod account and store baseline
grantaxis init --output baseline.yml --creds creds.json

# 2. later – detect drift by comparing live prod to baseline
grantaxis diff --baseline baseline.yml --report drift.md --creds creds.json

# 3. or diff against a pre‑captured snapshot
grantaxis diff --baseline baseline.yml --snapshot snapshot.json
```

**Credentials**
* For MVP: pass Snowflake connector kwargs as a **JSON file**.
* Environment variable `SNOWFLAKE_CREDS_JSON` overrides `--creds`.
"""


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Exit codes
EXIT_SUCCESS = 0
EXIT_DRIFT_DETECTED = 2
EXIT_ERROR = 1

if TYPE_CHECKING:
    import snowflake.connector


class CredentialsError(Exception):
    """Raised when credential loading fails."""

    pass


class SnapshotError(Exception):
    """Raised when snapshot operations fail."""

    pass


class BaselineError(Exception):
    """Raised when baseline operations fail."""

    pass


###############################################################################
# 1.  Credentials helper: env-vars → file → interactive
###############################################################################
ENV_VARS = (
    "SNOWFLAKE_USER",
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_AUTHENTICATOR",
    "SNOWFLAKE_PRIVATE_KEY_PATH",
)


def _load_creds(creds_path: Optional[str]) -> Dict[str, Any]:
    """
    Load Snowflake credentials in this order:
       1. All required env-vars present              (no prompt)
       2. JSON file via --creds                      (no prompt)
       3. Interactive prompt (password hidden)       (last resort)
    """
    # 1️⃣  Environment variables (user + account + any auth secret)
    env = {k: os.getenv(k) for k in ENV_VARS if os.getenv(k)}
    if {"SNOWFLAKE_USER", "SNOWFLAKE_ACCOUNT"} <= env.keys() and len(env) >= 3:
        logger.debug("Using credentials from environment variables")
        return _normalise_env_creds(env)

    # 2️⃣  JSON file
    if creds_path:
        try:
            with Path(creds_path).open(encoding="utf-8") as fh:
                data = json.load(fh)
            return _validate_creds_dict(data)
        except Exception as exc:
            raise CredentialsError(
                f"Failed to load credentials file {creds_path}: {exc}\n"
                "Example file:\n"
                + dedent(
                    """\
                {
                  "user": "myuser",
                  "account": "myaccount.region",
                  "password": "*****"
                }"""
                )
            ) from exc

    # 3️⃣  Interactive prompt
    click.echo("🔑  No credentials supplied – interactive login", err=True)
    user = click.prompt("Snowflake user")
    account = click.prompt("Snowflake account (e.g. acme-xy123)")
    password = getpass.getpass(
        "Snowflake password (or press ↵ to launch browser auth): "
    )

    creds: Dict[str, Any] = {"user": user, "account": account}
    if password:
        creds["password"] = password
    else:
        creds["authenticator"] = "externalbrowser"

    return _validate_creds_dict(creds)


# --------------------------------------------------------------------------- #
def _validate_creds_dict(creds: Dict[str, Any]) -> Dict[str, Any]:
    """Common validation used by all credential sources."""
    required = {"user", "account"}
    if not required <= creds.keys():
        raise CredentialsError(f"Missing required keys: {required - creds.keys()}")

    auth_ok = any(
        k in creds
        for k in (
            "password",
            "authenticator",
            "private_key",
            "private_key_path",
            "token",
        )
    )
    if not auth_ok:
        raise CredentialsError(
            "Missing authentication method.\n"
            "Provide one of: password, authenticator,\n"
            "private_key, private_key_path, token"
        )
    return creds


def _normalise_env_creds(env: Dict[str, str]) -> Dict[str, Any]:
    """Convert SNOWFLAKE_* env vars to connector kwargs."""
    mapping = {
        "SNOWFLAKE_USER": "user",
        "SNOWFLAKE_ACCOUNT": "account",
        "SNOWFLAKE_PASSWORD": "password",
        "SNOWFLAKE_AUTHENTICATOR": "authenticator",
        "SNOWFLAKE_PRIVATE_KEY_PATH": "private_key_path",
    }
    return {mapping[k]: v for k, v in env.items()}


def _ensure_snowflake_connector():
    """
    Ensure snowflake-connector-python is available.

    Raises:
        ImportError: If snowflake-connector-python is not installed
    """
    try:
        import snowflake.connector

        return snowflake.connector
    except ImportError as exc:
        raise ImportError(
            "snowflake-connector-python not installed. "
            "Install with: pip install snowflake-connector-python"
        ) from exc


def get_records_from_snapshot(
    ctx: "snowflake.connector.SnowflakeConnection",
) -> List[Dict[str, Any]]:
    """Return only the grant records from ``compile_snapshot``."""
    from grantaxis.snapshot import compile_snapshot

    snapshot = compile_snapshot(ctx)
    return snapshot["grants"]


def _capture_live_snapshot(creds_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Capture a live snapshot from Snowflake.

    Args:
        creds_dict: Snowflake connection parameters

    Returns:
        List of grant records

    Raises:
        SnapshotError: If snapshot capture fails
    """
    snowflake_connector = _ensure_snowflake_connector()

    try:
        logger.info("Connecting to Snowflake...")
        with snowflake_connector.connect(**creds_dict) as ctx:
            logger.info("Capturing snapshot...")
            records = get_records_from_snapshot(ctx)
            logger.info(f"Captured {len(records)} grant records")
            return records
    except Exception as exc:
        raise SnapshotError(f"Failed to capture live snapshot: {exc}") from exc


def _load_snapshot_file(snapshot_path: str) -> List[Dict[str, Any]]:
    """
    Load snapshot data from file (YAML or JSON).

    Args:
        snapshot_path: Path to snapshot file

    Returns:
        List of grant records

    Raises:
        SnapshotError: If snapshot file cannot be loaded
    """
    path = Path(snapshot_path)
    if not path.exists():
        raise SnapshotError(f"Snapshot file not found: {path}")

    try:
        logger.info(f"Loading snapshot from file: {path}")

        if path.suffix.lower() in {".yaml", ".yml"}:
            with path.open("r", encoding="utf-8") as f:
                snap_data = yaml.safe_load(f)

            # Handle both wrapped and unwrapped formats
            if isinstance(snap_data, dict) and "grants" in snap_data:
                records = snap_data["grants"]
            else:
                records = snap_data
        else:
            # Assume JSON format
            with path.open("r", encoding="utf-8") as f:
                records = json.load(f)

        if not isinstance(records, list):
            raise SnapshotError("Snapshot file must contain a list of grant records")

        logger.info(f"Loaded {len(records)} records from snapshot file")
        return records

    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Invalid format in snapshot file {path}: {exc}") from exc
    except (OSError, IOError) as exc:
        raise SnapshotError(f"Cannot read snapshot file {path}: {exc}") from exc


def write_detailed_baseline(snapshot: Dict[str, Any], outfile: Path) -> None:
    """Write the full snapshot to a separate YAML file."""
    import yaml
    from collections import OrderedDict
    from hashlib import sha256

    snapshot_id = sha256(
        "".join(g["id"] for g in snapshot["grants"]).encode()
    ).hexdigest()

    detailed_output = OrderedDict(
        [
            ("snapshot_id", snapshot_id),
            ("metadata", snapshot.get("snapshot_metadata")),
            ("users", snapshot.get("users")),
            ("roles", snapshot.get("roles")),
            ("grants", snapshot.get("grants")),
        ]
    )

    with open(outfile, "w", encoding="utf-8") as fh:
        yaml.safe_dump(detailed_output, fh, sort_keys=False, default_flow_style=False)

    logger.info(f"Detailed baseline written → {outfile}")


@click.group(help="GrantAxis – Snowflake RBAC baseline & drift CLI")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Root command group."""
    # Store verbose flag in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@cli.command(help="Snapshot live Snowflake account and write baseline YAML")
@click.option(
    "--creds",
    type=click.Path(exists=False, dir_okay=False),
    help="Snowflake credentials file (JSON) or '-' for interactive prompt",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    default="baseline.yml",
    show_default=True,
    help="Baseline YAML file to write",
)
@click.option(
    "--backup/--no-backup",
    default=True,
    show_default=True,
    help="Create backup of existing output file",
)
@click.pass_context
def init(ctx: click.Context, creds: Optional[str], output: str, backup: bool) -> None:
    """Initialize baseline by capturing current Snowflake grants."""
    try:
        # Load credentials
        creds_dict = _load_creds(creds)

        # Capture snapshot
        click.echo("📸 Capturing live snapshot...", err=True)
        records = _capture_live_snapshot(creds_dict)

        # Write baseline
        logger.info(f"Writing baseline to {output}")
        dump_baseline(records, output, backup=backup)

        click.echo(f"✅ Baseline written → {output} ({len(records)} grants)")

    except (CredentialsError, SnapshotError) as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(EXIT_ERROR)
    except Exception as exc:
        logger.exception("Unexpected error during init")
        click.echo(f"❌ Unexpected error: {exc}", err=True)
        sys.exit(EXIT_ERROR)


@cli.command(name="diff", help="Compare baseline vs snapshot (file or live)")
@click.option(
    "--baseline",
    "-b",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to baseline YAML file",
)
@click.option(
    "--snapshot",
    "-s",
    type=click.Path(dir_okay=False),
    help="Optional snapshot file (YAML/JSON). If omitted, live snapshot is captured",
)
@click.option(
    "--creds",
    type=click.Path(exists=False, dir_okay=False),
    help="Snowflake credentials file (JSON) or '-' for interactive prompt",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(dir_okay=False),
    show_default=True,
    help="Filter configuration YAML file",
)
@click.option(
    "--report",
    "-r",
    default="drift_report.md",
    show_default=True,
    help="Markdown report output file",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress console output")
@click.option(
    "--fail-on-drift/--no-fail-on-drift",
    default=True,
    show_default=True,
    help="Exit with code 2 when drift is detected",
)
@click.option(
    "--preset",
    type=str,
    help="Name of filter preset to apply (from grantaxis.yml or built-in)",
)
@click.pass_context
def diff_cmd(
    ctx: click.Context,
    baseline: str,
    snapshot: Optional[str],
    creds: Optional[str],
    config: Optional[str],
    report: str,
    quiet: bool,
    fail_on_drift: bool,
    preset: Optional[str],
) -> None:
    """Compare baseline against current state and generate drift report."""
    try:
        # Load baseline
        logger.info(f"Loading baseline from {baseline}")
        try:
            baseline_data = load_baseline(baseline)
            base_records = baseline_data["grants"]
            logger.info(f"Loaded {len(base_records)} baseline records")
        except Exception as exc:
            raise BaselineError(
                f"Failed to load baseline from {baseline}: {exc}"
            ) from exc

        # Load snapshot (from file or live capture)
        if snapshot:
            snap_records = _load_snapshot_file(snapshot)
        else:
            creds_dict = _load_creds(creds)  # env / file / interactive
            if not quiet:
                click.echo("📸 Capturing live snapshot...", err=True)
            snap_records = _capture_live_snapshot(creds_dict)

        cfg_path = config or (
            "grantaxis.yml" if Path("grantaxis.yml").exists() else None
        )
        cfg = Config.load(cfg_path, preset_override=preset)

        if config:
            logger.info(f"Using configuration: {config}")
        elif cfg_path:
            logger.info(f"Auto-discovered {cfg_path}")
        else:
            logger.info("Using built-in preset only (no config file)")

        # Perform diff
        logger.info("Computing differences...")
        added, removed, changed, transfers = diff_records(base_records, snap_records)

        # Apply filters
        # ── Apply config filters (transfers unchanged for now) ──────────
        original_counts = (len(added), len(removed), len(changed), len(transfers))
        added, removed, changed, transfers = cfg.filter_drift(
            added, removed, changed, transfers
        )
        filtered_counts = (len(added), len(removed), len(changed), len(transfers))

        if original_counts != filtered_counts:
            logger.info(f"Filtered: {original_counts} → {filtered_counts}")

        # Generate report
        logger.info(f"Generating report: {report}")
        markdown_report = render_markdown(added, removed, changed, transfers)

        report_path = Path(report)
        report_path.write_text(markdown_report, encoding="utf-8")

        # ── Console output ──────────────────────────────────────────────
        if not quiet:
            drift_detected = bool(added or removed or changed or transfers)
            if drift_detected:
                summary = (
                    f"🚨 Drift detected: "
                    f"+{len(added)} -{len(removed)} ~{len(changed)} 🔄{len(transfers)}"
                )
                click.echo(summary)
            else:
                click.echo("✅ No drift detected")
            click.echo(f"📄 Report written → {report}")

        # ── Exit code logic ─────────────────────────────────────────────
        if added or removed or changed or transfers:
            if fail_on_drift:
                sys.exit(EXIT_DRIFT_DETECTED)
        else:
            sys.exit(EXIT_SUCCESS)

    except (CredentialsError, SnapshotError, BaselineError) as exc:
        click.echo(f"❌ {exc}", err=True)
        sys.exit(EXIT_ERROR)
    except Exception as exc:
        logger.exception("Unexpected error during diff")
        click.echo(f"❌ Unexpected error: {exc}", err=True)
        sys.exit(EXIT_ERROR)


@cli.command(help="Validate configuration file")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False),
    default="grantaxis.yml",
    show_default=True,
    help="Configuration file to validate",
)
def validate(config: str) -> None:
    """Validate configuration file syntax and structure."""
    try:
        cfg = Config.load(config)
        stats = cfg.get_stats()

        click.echo(f"✅ Configuration valid: {config}")
        click.echo(f"📊 Pattern counts: {stats}")

    except ConfigError as exc:
        click.echo(f"❌ Configuration error: {exc}", err=True)
        sys.exit(EXIT_ERROR)
    except Exception as exc:
        logger.exception("Unexpected error during validation")
        click.echo(f"❌ Unexpected error: {exc}", err=True)
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    cli()
