from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import yaml

from grantaxis.baseline import load_baseline, BaselineValidationError

"""
GrantAxis – diff.py (v1.3)
=========================
Drift detector with:
* Set‑based comparison for added / removed / grant‑option flips.
* Role transfer detection for privilege reassignments.
* Markdown summary + counts (pipes escaped).
* Snapshot loader with robust error handling.
* Optional performance timing; CLI exit codes 0/1/2.
"""


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
Record = Dict[str, Any]
ChangedPair = Tuple[Record, Record]
TransferPair = Tuple[Record, Record]  # (from_record, to_record)

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = {"privilege", "grantee_type", "grantee_name"}


def _validate_records(recs: Sequence[Record], src: str) -> None:
    for idx, r in enumerate(recs):
        missing = REQUIRED_FIELDS - r.keys()
        if missing:
            raise ValueError(f"{src} record {idx} missing fields: {missing}")


def _identity_key(rec: Record) -> str:
    """Full identity key including grantee for exact matching."""
    parts = (
        rec.get("database_name"),
        rec.get("schema_name"),
        rec.get("object_type"),
        rec.get("object_name"),
        rec.get("privilege"),
        rec.get("grantee_type"),
        rec.get("grantee_name"),
        rec.get("source", ""),
    )
    return (
        "|".join("")
        if parts is None
        else "|".join("" if p is None else str(p) for p in parts)
    )


def _transfer_key(rec: Record) -> str:
    """Key for matching transfers - same object/privilege, different grantee."""
    parts = (
        rec.get("database_name"),
        rec.get("schema_name"),
        rec.get("object_type"),
        rec.get("object_name"),
        rec.get("privilege"),
        rec.get("source", ""),
    )
    return (
        "|".join("")
        if parts is None
        else "|".join("" if p is None else str(p) for p in parts)
    )


def _escape_md(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _fmt_obj(rec: Record) -> str:
    if rec.get("object_type") == "ACCOUNT":
        return "ACCOUNT"
    db, sch, obj = (
        rec.get("database_name", ""),
        rec.get("schema_name", ""),
        rec.get("object_name", ""),
    )
    return _escape_md(".".join(p for p in (db, sch, obj) if p))


# ---------------------------------------------------------------------------
# Core diff
# ---------------------------------------------------------------------------


def diff_records(
    baseline: Sequence[Record], snapshot: Sequence[Record]
) -> Tuple[List[Record], List[Record], List[ChangedPair], List[TransferPair]]:
    t0 = time.perf_counter()

    base_map = {(_identity_key(r)): r for r in baseline}
    snap_map = {(_identity_key(r)): r for r in snapshot}

    added_keys = snap_map.keys() - base_map.keys()
    removed_keys = base_map.keys() - snap_map.keys()
    common_keys = snap_map.keys() & base_map.keys()

    added = [snap_map[k] for k in added_keys]
    removed = [base_map[k] for k in removed_keys]
    changed: List[ChangedPair] = []

    # Handle grant option changes for common records
    for k in common_keys:
        b, s = base_map[k], snap_map[k]
        if b.get("with_grant_option", False) != s.get("with_grant_option", False):
            changed.append((b, s))

    # Detect role transfers
    transfers: List[TransferPair] = []

    # Group removed and added records by transfer key (object + privilege)
    removed_by_transfer_key = {}
    added_by_transfer_key = {}

    for rec in removed:
        transfer_key = _transfer_key(rec)
        if transfer_key not in removed_by_transfer_key:
            removed_by_transfer_key[transfer_key] = []
        removed_by_transfer_key[transfer_key].append(rec)

    for rec in added:
        transfer_key = _transfer_key(rec)
        if transfer_key not in added_by_transfer_key:
            added_by_transfer_key[transfer_key] = []
        added_by_transfer_key[transfer_key].append(rec)

    # Find matching transfers and remove them from added/removed lists
    final_added = []
    final_removed = []

    for transfer_key in removed_by_transfer_key:
        if transfer_key in added_by_transfer_key:
            # We have both removals and additions for the same object+privilege
            removed_recs = removed_by_transfer_key[transfer_key]
            added_recs = added_by_transfer_key[transfer_key]

            # Match up transfers (simple 1:1 matching for now)
            min_count = min(len(removed_recs), len(added_recs))
            for i in range(min_count):
                from_rec = removed_recs[i]
                to_rec = added_recs[i]
                # Only consider it a transfer if grantees are different
                if from_rec.get("grantee_name") != to_rec.get("grantee_name"):
                    transfers.append((from_rec, to_rec))

            # Add any remaining unmatched records back to final lists
            final_removed.extend(removed_recs[min_count:])
            final_added.extend(added_recs[min_count:])
        else:
            # No matching additions, these are true removals
            final_removed.extend(removed_by_transfer_key[transfer_key])

    # Add records that had additions but no matching removals
    for transfer_key in added_by_transfer_key:
        if transfer_key not in removed_by_transfer_key:
            final_added.extend(added_by_transfer_key[transfer_key])

    elapsed = time.perf_counter() - t0
    if elapsed > 1.0:  # log only if non‑trivial
        print(f"Diff completed in {elapsed:.2f}s", file=sys.stderr)

    return final_added, final_removed, changed, transfers


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
RISK_EMOJI = {"HIGH": "🔴", "MED": "🟡", "LOW": "🟢"}


def risk_level(rec: Record) -> str:
    db = rec.get("database_name", "")
    priv = rec.get("privilege", "")
    if db.startswith(("PRD", "PROD")) and priv in {"OWNERSHIP", "DROP", "DELETE"}:
        return "HIGH"
    if priv in {"INSERT", "UPDATE", "MODIFY"}:
        return "MED"
    return "LOW"


def biz_context(rec: Record) -> str:
    ctx = []
    if rec.get("database_name", "").startswith(("PRD", "PROD")):
        ctx.append("PROD data")
    if rec["privilege"] in {"DROP", "DELETE", "TRUNCATE"}:
        ctx.append("destructive")
    if "SERVICE" in rec.get("grantee_name", ""):
        ctx.append("service acct")
    return ", ".join(ctx)


def render_markdown(
    added: List[Record],
    removed: List[Record],
    changed: List[ChangedPair],
    transfers: List[TransferPair],
) -> str:
    total = len(added) + len(removed) + len(changed) + len(transfers)
    if total == 0:
        return "No drift detected."

    high = sum(risk_level(r) == "HIGH" for r in added + removed)
    med = sum(risk_level(r) == "MED" for r in added + removed)
    low = total - high - med

    lines = [
        "# Grant Drift Report",
        "",
        f"**Summary:** {total} changes ({RISK_EMOJI['HIGH']} {high}  {RISK_EMOJI['MED']} {med}  {RISK_EMOJI['LOW']} {low})",
        "",
    ]

    # Regular changes table
    if added or removed or changed:
        lines.extend(
            [
                "| Type | Grantee | Object | Priv | GrantOpt | Risk | Context |",
                "|------|---------|--------|------|----------|------|---------|",
            ]
        )

        # --- Added
        for rec in added:
            r_lvl = risk_level(rec)
            lines.append(
                f"| ➕ Added | {_escape_md(rec['grantee_name'])} | "
                f"{_fmt_obj(rec)} | {_escape_md(rec['privilege'])} | "
                f"{rec.get('with_grant_option', False)} | {RISK_EMOJI[r_lvl]} | {biz_context(rec)} |"
            )
        # --- Removed
        for rec in removed:
            r_lvl = risk_level(rec)
            lines.append(
                f"| ➖ Removed | {_escape_md(rec['grantee_name'])} | "
                f"{_fmt_obj(rec)} | {_escape_md(rec['privilege'])} | "
                f"{rec.get('with_grant_option', False)} | {RISK_EMOJI[r_lvl]} | {biz_context(rec)} |"
            )
        # --- Changed (grant‑option flip only)
        for b, s in changed:
            r_lvl = risk_level(s)
            lines.append(
                f"| ➜ Changed | {_escape_md(b['grantee_name'])} | "
                f"{_fmt_obj(b)} | {_escape_md(b['privilege'])} | "
                f"{b.get('with_grant_option')}→{s.get('with_grant_option')} | {RISK_EMOJI[r_lvl]} | Grant option flip |"
            )
        lines.append("")

    # Role transfers table (kept simple)
    if transfers:
        lines.extend(
            [
                "## 🔄 Role Transfers",
                "| Object | Privilege | From → To | GrantOpt | Context |",
                "|--------|-----------|-----------|----------|---------|",
            ]
        )
        for from_rec, to_rec in transfers:
            lines.append(
                f"| {_fmt_obj(from_rec)} | {_escape_md(from_rec['privilege'])} | "
                f"{_escape_md(from_rec['grantee_name'])} → {_escape_md(to_rec['grantee_name'])} | "
                f"{from_rec.get('with_grant_option', False)} | Role reassignment |"
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot loader
# ---------------------------------------------------------------------------


def _load_snapshot(path: Path) -> List[Record]:
    try:
        if path.suffix in {".yaml", ".yml"}:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "grants" in data:
                    data = data["grants"]
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
    except FileNotFoundError as e:
        print(f"Snapshot file not found: {path}", file=sys.stderr)
        raise SystemExit(1) from e
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        print(f"Snapshot load error: {e}", file=sys.stderr)
        raise SystemExit(1) from e

    if not isinstance(data, list):
        print("Snapshot must be a list of grant records", file=sys.stderr)
        raise SystemExit(1)
    return data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="GrantAxis baseline vs snapshot drift detector",
        epilog="Exit codes: 0=no drift, 1=error, 2=drift detected",
    )
    parser.add_argument("baseline", help="baseline.yaml from grantaxis init")
    parser.add_argument("snapshot", help="snapshot YAML/JSON produced by scan")
    parser.add_argument(
        "--report", "-r", default="drift_report.md", help="Markdown output file"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress stdout summary"
    )
    args = parser.parse_args()

    try:
        base_records = load_baseline(args.baseline)["grants"]
    except (FileNotFoundError, BaselineValidationError, ValueError) as exc:
        print("Baseline load error:", exc, file=sys.stderr)
        sys.exit(1)

    snap_records = _load_snapshot(Path(args.snapshot))

    _validate_records(base_records, "baseline")
    _validate_records(snap_records, "snapshot")

    added, removed, changed, transfers = diff_records(base_records, snap_records)
    md = render_markdown(added, removed, changed, transfers)
    Path(args.report).write_text(md, encoding="utf-8")

    if not args.quiet:
        # concise console output
        console_output = (
            md if md == "No drift detected." else md.split("\n", 5)[0] + "\n…"
        )
        print(console_output)
        print(f"Report written → {args.report}")

    sys.exit(2 if (added or removed or changed or transfers) else 0)


if __name__ == "__main__":
    _cli()
