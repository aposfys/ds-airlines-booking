import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set before importing app.config, which validates it at import time.
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-to-pass-32")

from app.auth import get_password_hash  # noqa: E402
from app.routers.auth import PASSWORD_FIELD  # noqa: E402
from tests.fake_mongo import FakeDB  # noqa: E402

REGULAR_PASSWORD = "passenger123"
ADMIN_PASSWORD = "administrator1"


@pytest_asyncio.fixture
async def fake_db(monkeypatch):
    """Swap the shared Motor handle for an in-memory fake.

    Every module binds `db` at import time (`from app.database import db`),
    so each binding has to be patched individually.
    """
    db = FakeDB()
    for module in (
        "app.database",
        "app.auth",
        "app.seed",
        "app.routers.auth",
        "app.routers.admin",
        "app.routers.flights",
        "app.routers.bookings",
    ):
        monkeypatch.setattr(f"{module}.db", db, raising=False)

    # Uniqueness of email, username and flight code is enforced only by these
    # indexes — the handlers rely on catching DuplicateKeyError rather than
    # checking first. httpx's ASGITransport does not run lifespan events, so
    # without this the tests would exercise a database with no constraints at
    # all and duplicate-rejection tests would silently pass nothing.
    from app.database import ensure_indexes

    await ensure_indexes()
    return db


@pytest_asyncio.fixture
async def client(fake_db):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _make_user(fake_db, *, email, username, password, is_admin=False):
    await fake_db.users.insert_one(
        {
            "email": email,
            "username": username,
            "fullname": "Test Passenger" if not is_admin else "Test Admin",
            "passport_num": "AB123456",
            PASSWORD_FIELD: get_password_hash(password),
            "is_admin": is_admin,
            "is_active": True,
        }
    )


@pytest_asyncio.fixture
async def passenger(fake_db):
    await _make_user(
        fake_db,
        email="passenger@example.com",
        username="passenger",
        password=REGULAR_PASSWORD,
    )
    return {"username": "passenger", "password": REGULAR_PASSWORD}


@pytest_asyncio.fixture
async def admin(fake_db):
    await _make_user(
        fake_db,
        email="ops@dsairlines.example",
        username="ops",
        password=ADMIN_PASSWORD,
        is_admin=True,
    )
    return {"username": "ops", "password": ADMIN_PASSWORD}


@pytest_asyncio.fixture
async def auth_header(client):
    async def _login(credentials: dict) -> dict:
        response = await client.post("/api/auth/login", json=credentials)
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest_asyncio.fixture
async def flight(fake_db):
    doc = {
        "unique_code": "ATHLHR26081510",
        "departure": "Athens (ATH)",
        "destination": "London (LHR)",
        "date": "2026-08-15",
        "time": "10:30",
        "cost": 185.50,
        "duration": "3h 45m",
        "availability": 220,
    }
    await fake_db.availableFlights.insert_one(doc)
    return doc
