from __future__ import annotations
import json
import logging
import os
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

"""
GrantAxis – conn.py (Enterprise Edition v0.1.1)
==============================================
Snowflake connection helper with:
* **SSO via external browser** fallback when no secret is provided.
* Key‑pair support (`private_key` or `private_key_path`).
* Exponential‑back‑off retry (network only).
* Comprehensive `test_connection` returning environment metadata.
* Pluggable profile loader (`~/.snowflake/connections.yml`, env override).

Focus for this patch: tighten edge‑cases, remove dead imports, align kwargs
with Snowflake connector API.
"""


logger = logging.getLogger(__name__)

try:
    import snowflake.connector as sf
    from snowflake.connector import DictCursor
except ImportError:  # deferred error until first use
    sf = None  # type: ignore
    DictCursor = None  # type: ignore

try:
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    CRYPTO = True
except ImportError:
    CRYPTO = False
    logger.debug("cryptography not available – private‑key validation skipped")

__all__ = [
    "SnowflakeConnectionError",
    "SnowflakeAuthenticationError",
    "SnowflakeNetworkError",
    "SnowflakeConfigurationError",
    "connect",
    "connection_context",
    "test_connection",
    "load_connection_profile",
]

# ───────────────────────────── Exceptions ──────────────────────────────── #


class SnowflakeConnectionError(RuntimeError):
    """Generic connection failure."""


class SnowflakeAuthenticationError(SnowflakeConnectionError):
    """Invalid creds / SSO rejected."""


class SnowflakeNetworkError(SnowflakeConnectionError):
    """DNS / TLS / TCP issues."""


class SnowflakeConfigurationError(SnowflakeConnectionError):
    """Bad creds dict or profile."""


# ───────────────────────────── Helpers ─────────────────────────────────── #


_SENSITIVE_KEYS = {
    "password",
    "private_key",
    "private_key_passphrase",
    "token",
    "oauth_token",
}


def _safe_log(obj: Dict[str, Any]) -> Dict[str, Any]:
    return {k: ("***" if k in _SENSITIVE_KEYS else v) for k, v in obj.items()}


def _validate_pkey(buf: bytes, passphrase: str | None) -> None:
    if not CRYPTO:
        return
    from cryptography.hazmat.backends import default_backend  # type: ignore

    try:
        load_pem_private_key(
            buf,
            password=passphrase.encode() if passphrase else None,
            backend=default_backend(),
        )
    except Exception as exc:  # pragma: no cover
        raise SnowflakeConfigurationError(
            f"Private key validation " f"failed: {exc}"
        ) from exc


def _categorise(exc: Exception) -> SnowflakeConnectionError:
    msg = str(exc).lower()
    if any(
        t in msg
        for t in ("auth", "invalid password", "incorrect username", "private key")
    ):
        return SnowflakeAuthenticationError(str(exc))
    if any(t in msg for t in ("timeout", "network", "could not connect", "dns")):
        return SnowflakeNetworkError(str(exc))
    return SnowflakeConnectionError(str(exc))


# ───────────────────────────── Retry decorator ──────────────────────────── #


def retryable(func):
    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[override]
        creds = kwargs.get("creds") or (args[0] if args else {})
        attempts = int(creds.get("retry_attempts", 3))
        backoff = float(creds.get("retry_backoff", 1.0))
        last_exc: Exception | None = None
        for i in range(attempts):
            try:
                return func(*args, **kwargs)
            except SnowflakeNetworkError as exc:
                last_exc = exc
                if i < attempts - 1:
                    wait = backoff * 2**i
                    logger.warning(
                        "Network error – retry %d/%d in %.1fs: %s",
                        i + 1,
                        attempts,
                        wait,
                        exc,
                    )
                    time.sleep(wait)
            except SnowflakeAuthenticationError:
                raise  # don’t retry creds issues
        if last_exc:
            raise last_exc

    return wrapper


# ───────────────────────────── Credential prep ──────────────────────────── #


def _prepare_kwargs(creds: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(creds, dict):
        raise SnowflakeConfigurationError("Credentials must be a dict")

    base = creds.copy()
    user = base.get("user")
    account = base.get("account")
    if not user or not account:
        raise SnowflakeConfigurationError("'user' and 'account' are required")

    # private‑key path → bytes
    if "private_key_path" in base:
        pk_path = Path(base.pop("private_key_path"))
        if not pk_path.exists():
            raise SnowflakeConfigurationError(f"Private key file not found: {pk_path}")
        pk_bytes = pk_path.read_bytes()
        _validate_pkey(pk_bytes, base.get("private_key_passphrase"))
        base["private_key"] = pk_bytes

    if "private_key" in base and isinstance(base["private_key"], str):
        pk_bytes = base["private_key"].encode()
        _validate_pkey(pk_bytes, base.get("private_key_passphrase"))
        base["private_key"] = pk_bytes

    # choose authenticator automatically
    auth = base.pop("authenticator", None)
    if auth is None:
        if any(k in base for k in ("password", "private_key", "token")):
            auth = "snowflake"  # default internal
        else:
            auth = "externalbrowser"
    base["authenticator"] = auth

    # default timeouts
    base.setdefault("login_timeout", int(base.get("connect_timeout", 60)))
    base.setdefault("network_timeout", int(base.get("network_timeout", 300)))
    if auth == "externalbrowser":
        base.setdefault("browser_timeout", int(base.get("browser_timeout", 120)))

    # remove client‑only keys
    for k in ("retry_attempts", "retry_backoff", "private_key_passphrase"):
        base.pop(k, None)
    return base


# ───────────────────────────── Connection API ───────────────────────────── #


@retryable
def connect(creds: Dict[str, Any]):  # -> sf.SnowflakeConnection
    """Open a Snowflake connection; raises categorised exceptions."""
    if sf is None:  # pragma: no cover
        raise ImportError("snowflake-connector-python not installed")

    kwargs = _prepare_kwargs(creds)
    logger.debug("Connecting with %s", _safe_log(kwargs))
    try:
        return sf.connect(**kwargs)  # type: ignore[arg-type]
    except Exception as exc:  # pragma: no cover – connector raises many types
        raise _categorise(exc) from exc


@contextmanager
def connection_context(creds: Dict[str, Any]):  # type: ignore[override]
    conn = connect(creds)
    try:
        yield conn
    finally:
        try:
            conn.close()
            logger.debug("Snowflake connection closed")
        except Exception:  # pragma: no cover
            logger.debug("Error closing connection", exc_info=True)


# ───────────────────────────── Test connection ──────────────────────────── #


def test_connection(creds: Dict[str, Any]) -> Dict[str, Any]:
    start = time.perf_counter()
    info: Dict[str, Any] = {"status": "failed"}
    try:
        with connection_context(creds) as conn:
            cur = conn.cursor(DictCursor)  # type: ignore[arg-type]
            cur.execute("SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE()")
            acc, usr, role = cur.fetchone().values()
            info.update(status="connected", account=acc, user=usr, current_role=role)
            cur.close()
        info["latency_sec"] = round(time.perf_counter() - start, 3)
    except SnowflakeConnectionError as exc:
        info.update(
            error=str(exc),
            error_type=type(exc).__name__,
            latency_sec=round(time.perf_counter() - start, 3),
        )
    return info


# ───────────────────────────── Profile loader ───────────────────────────── #


def load_connection_profile(name: str = "default") -> Dict[str, Any]:
    env = os.getenv(f"SNOWFLAKE_PROFILE_{name.upper()}")
    if env:
        try:
            return json.loads(env)
        except json.JSONDecodeError as exc:
            raise SnowflakeConfigurationError(
                f"Bad JSON in env var for profile " f"{name}: {exc}"
            ) from exc

    candidates = [
        Path.home() / ".snowflake" / "connections.yml",
        Path.home() / ".config" / "snowflake" / "connections.yml",
        Path("snowflake_connections.yml"),
        Path("connections.yml"),
    ]
    for p in candidates:
        if p.exists():
            try:
                data = yaml.safe_load(p.read_text()) or {}
                if isinstance(data, dict) and name in data:
                    return data[name]
            except Exception as exc:  # pragma: no cover
                logger.debug("Unable to read %s: %s", p, exc)
    raise SnowflakeConfigurationError(f"Connection profile '{name}' not found")


# ───────────────────────────── Permission helper ────────────────────────── #


def validate_connection_permissions(
    conn, required_roles: List[str] | None = None
) -> Tuple[bool, List[str]]:  # noqa: D401
    if not required_roles:
        return True, []
    try:
        cur = conn.cursor()
        cur.execute("SHOW ROLES")
        available = {row[1] for row in cur.fetchall()}
        cur.close()
        missing = [r for r in required_roles if r not in available]
        return len(missing) == 0, missing
    except Exception as exc:  # pragma: no cover
        logger.debug("validate_connection_permissions error: %s", exc)
        return False, required_roles
