"""Application configuration.

Settings are read from the environment once, at import time, and validated
immediately. A missing or weak SECRET_KEY raises here rather than silently
falling back to a default — a hardcoded fallback key means every deployment
that forgets to set one shares a signing key that is public on GitHub, and
anyone can mint a valid admin token for it.
"""

import os
import secrets

from dotenv import load_dotenv

load_dotenv()

# A key shorter than this is not worth the false confidence.
_MIN_SECRET_KEY_LENGTH = 32

# Rejected outright: these are the values that shipped in the source or are
# the obvious things to type when the app refuses to start.
_KNOWN_WEAK_KEYS = {
    "your-super-secret-key-change-this-in-prod",
    "secret",
    "changeme",
    "development",
    "test",
}


def _require_secret_key() -> str:
    key = os.environ.get("SECRET_KEY", "").strip()

    # Tests and local tooling need to import the app without a .env file.
    # An ephemeral per-process key is safe: it cannot be shared, and every
    # restart invalidates previously issued tokens.
    if not key and os.environ.get("PYTEST_CURRENT_TEST"):
        return secrets.token_urlsafe(48)

    if not key:
        raise RuntimeError(
            "SECRET_KEY is not set. Copy .env.example to .env and generate one:\n"
            '  python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
    if key in _KNOWN_WEAK_KEYS:
        raise RuntimeError(
            "SECRET_KEY is a known placeholder value. Generate a real one:\n"
            '  python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
    if len(key) < _MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f"SECRET_KEY must be at least {_MIN_SECRET_KEY_LENGTH} characters "
            f"(got {len(key)})."
        )
    return key


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY: str = _require_secret_key()
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# PostgreSQL from Phase 1 — see docs/adr/0001-postgresql-over-mongodb.md.
# The async driver is asyncpg; Alembic rewrites this to psycopg for its own
# synchronous connection.
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://dsairlines:dsairlines@localhost:5432/dsairlines"
)

# Log every statement. Useful locally, ruinous in production — it prints
# parameter values, which for this schema includes passenger names.
SQL_ECHO: bool = _env_flag("SQL_ECHO", default=False)

# Demo-data seeding is opt-in. It used to run unconditionally on every
# startup, including production, creating a known admin account.
SEED_ON_STARTUP: bool = _env_flag("SEED_ON_STARTUP", default=False)
SEED_ADMIN_EMAIL: str = os.environ.get("SEED_ADMIN_EMAIL", "").strip()
SEED_ADMIN_PASSWORD: str = os.environ.get("SEED_ADMIN_PASSWORD", "")
