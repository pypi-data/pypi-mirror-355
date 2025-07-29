from __future__ import annotations
import hashlib
import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Sequence
import yaml
from collections import OrderedDict


"""
GrantAxis – baseline.py (v1.3)
=============================
Deterministic YAML serializer / loader with strict validation, logging, and
robust edge‑case handling.

Incremental upgrades (v1.3)
---------------------------
* `_hash_records` casts each id to str → tolerant of non‑string hashes.
* Custom `BaselineValidationError` for all structural issues.
* Memory‑light `_is_sorted` to validate id order without `sorted()` copy.
* `logging` added for backup creation and load diagnostics.
* Constants extracted; type hints unified to `Sequence`.
"""

# ---------------------------------------------------------------------------
# Constants & logging
# ---------------------------------------------------------------------------
UTF8 = "utf-8"
NEWLINE = "\n"
DEFAULT_WIDTH = 80

log = logging.getLogger(__name__)
if not log.handlers:  # library style – configure if root not set
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class BaselineValidationError(ValueError):
    """Raised when baseline structure or order is invalid."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# Ensure OrderedDicts are YAML-safe
def represent_ordereddict(dumper, data):
    return dumper.represent_dict(data.items())


yaml.add_representer(OrderedDict, represent_ordereddict, Dumper=yaml.SafeDumper)


def _hash_records(records: Sequence[Dict[str, Any]]) -> str:
    ids_concat = "".join(str(rec["id"]) for rec in records)
    return hashlib.sha256(ids_concat.encode()).hexdigest()


def _is_sorted(ids: Sequence[str]) -> bool:
    return all(a <= b for a, b in zip(ids, ids[1:]))


def _validate_records(records: Sequence[Dict[str, Any]]) -> None:
    if not all(isinstance(r, dict) for r in records):
        raise BaselineValidationError("Each record must be a mapping/dict")

    missing = [i for i, r in enumerate(records) if "id" not in r]
    if missing:
        raise BaselineValidationError(f"Record(s) missing 'id' at positions {missing}")

    ids = [str(r["id"]) for r in records]
    if not _is_sorted(ids):
        raise BaselineValidationError("Records must be pre‑sorted by id ascending")


def _safe_backup(path: Path) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bkp = path.with_suffix(path.suffix + f".bak.{ts}")
    counter = 1
    while bkp.exists():
        bkp = path.with_suffix(path.suffix + f".bak.{ts}.{counter}")
        counter += 1
    path.rename(bkp)
    log.info("Created backup → %s", bkp)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def dump_baseline(
    records: Sequence[Dict[str, Any]],
    fp: io.TextIOBase | Path | str,
    *,
    backup: bool = False,
    line_width: int = DEFAULT_WIDTH,
) -> None:
    if not isinstance(records, (list, tuple)):
        raise TypeError("Records must be a list or tuple of dicts")

    _validate_records(records)

    payload = {
        "snapshot_id": _hash_records(records),
        "grants": list(records),
    }
    dump_args = {"sort_keys": True, "width": line_width}

    if isinstance(fp, (str, Path)):
        path = Path(fp)
        if backup and path.exists():
            _safe_backup(path)
        with open(path, "w", encoding=UTF8, newline=NEWLINE) as handle:
            yaml.safe_dump(payload, handle, **dump_args)
    else:
        yaml.safe_dump(payload, fp, **dump_args)


def load_baseline(fp: io.TextIOBase | Path | str) -> Dict[str, Any]:
    try:
        if isinstance(fp, (str, Path)):
            with open(fp, "r", encoding=UTF8) as handle:
                data = yaml.safe_load(handle)
        else:
            data = yaml.safe_load(fp)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Baseline file not found: {fp}") from e
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {e}") from e

    if not isinstance(data, dict):
        raise BaselineValidationError(
            "Baseline file must contain a YAML mapping/dictionary"
        )

    records = data.get("grants", [])
    _validate_records(records)

    expected = data.get("snapshot_id")
    recalculated = _hash_records(records)
    if expected != recalculated:
        raise BaselineValidationError("Baseline corrupted: snapshot_id mismatch")

    log.debug("Loaded baseline %s with %d records", expected, len(records))
    return data


# ---------------------------------------------------------------------------
# Smoke‑test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    dummy = [{"id": "a"}, {"id": "b"}]
    target = Path("baseline_test.yaml")

    dump_baseline(dummy, target, backup=True, line_width=120)
    print("Baseline written →", target)
    loaded = load_baseline(target)
    print("Reload OK", loaded["snapshot_id"])
