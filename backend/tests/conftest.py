"""Test fixtures backed by a real PostgreSQL database.

This replaces `tests/fake_mongo.py`, the in-memory stand-in built in Phase 0.
That fake was honest about being a bridge: tests passing against it were
evidence about our own logic, not about the database. ADR-001 promised to
retire it, and this is that.

The schema is built by running the Alembic migrations, not
`metadata.create_all`. That means every test run also proves the migration
chain applies cleanly — the drift between models and migrations that ADR-001
lists as a risk cannot go unnoticed.

Isolation: each test runs inside a transaction that is rolled back afterwards.
`join_transaction_mode="create_savepoint"` means the application's own commit
(in `get_session`) becomes a savepoint release rather than a real commit, so
handler code takes its normal path and the outer rollback still undoes
everything.
"""

import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Set before app.config is imported — it validates SECRET_KEY at import time.
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-to-pass-32")

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://dsairlines:dsairlines@localhost:5432/dsairlines_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

PASSENGER_PASSWORD = "passenger123"
ADMIN_PASSWORD = "administrator1"


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Build the schema once per session by running the migrations."""
    from alembic import command
    from alembic.config import Config

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield


@pytest_asyncio.fixture(scope="session")
async def engine(apply_migrations):
    eng = create_async_engine(TEST_DATABASE_URL)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncSession:
    connection = await engine.connect()
    transaction = await connection.begin()
    db = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield db
    finally:
        await db.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(session) -> AsyncClient:
    from app.db import get_session
    from main import app

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Domain fixtures ───────────────────────────────────────


@pytest_asyncio.fixture
async def reference_data(session):
    """Airports, aircraft, seat maps, routes and fare classes."""
    from app.seed import _seed_reference_data

    await _seed_reference_data(session)
    await session.flush()


@pytest_asyncio.fixture
async def passenger(session):
    from app.auth import get_password_hash
    from app.models.domain import User

    user = User(
        email="passenger@example.com",
        username="passenger",
        full_name="Test Passenger",
        passport_number="AB123456",
        hashed_password=get_password_hash(PASSENGER_PASSWORD),
        is_admin=False,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def admin(session):
    from app.auth import get_password_hash
    from app.models.domain import User

    user = User(
        email="ops@dsairlines.example",
        username="ops",
        full_name="Test Administrator",
        passport_number=None,
        hashed_password=get_password_hash(ADMIN_PASSWORD),
        is_admin=True,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
def auth_header(client):
    async def _login(username: str, password: str) -> dict:
        response = await client.post(
            "/api/auth/login", json={"username": username, "password": password}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest_asyncio.fixture
async def passenger_header(auth_header, passenger):
    return await auth_header("passenger", PASSENGER_PASSWORD)


@pytest_asyncio.fixture
async def admin_header(auth_header, admin):
    return await auth_header("ops", ADMIN_PASSWORD)


@pytest_asyncio.fixture
async def flight(session, reference_data):
    """One ATH–LHR flight with a materialised 220-seat cabin."""
    from datetime import date, datetime, time, timedelta, timezone
    from decimal import Decimal

    from sqlalchemy import select

    from app.models.domain import Aircraft, Flight, FlightSeat, Route, SeatMapEntry

    route = await session.scalar(
        select(Route).where(Route.origin_iata == "ATH", Route.destination_iata == "LHR")
    )
    aircraft = await session.scalar(select(Aircraft).where(Aircraft.registration == "SX-DLA"))

    departure = datetime.combine(
        date.today() + timedelta(days=14), time(10, 30), tzinfo=timezone.utc
    )
    f = Flight(
        flight_number="DS1040",
        route_id=route.id,
        aircraft_id=aircraft.id,
        departure_date=departure.date(),
        scheduled_departure=departure,
        scheduled_arrival=departure + route.scheduled_duration,
        base_fare_eur=Decimal("129.00"),
    )
    session.add(f)
    await session.flush()

    seat_map = (
        await session.scalars(
            select(SeatMapEntry).where(
                SeatMapEntry.aircraft_type_id == aircraft.aircraft_type_id
            )
        )
    ).all()
    session.add_all(
        FlightSeat(flight_id=f.id, seat_number=s.seat_number) for s in seat_map
    )
    await session.flush()
    return f
