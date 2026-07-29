"""Demo data seeding.

This used to run unconditionally on every application startup and create an
administrator with the password `admin`, hardcoded in this file and public on
GitHub. Any deployment of this code shipped with a known root account.

Seeding is now opt-in (SEED_ON_STARTUP) and has no default credentials: if
the environment does not supply both an email and a password, the admin is
not created and a warning is logged.
"""

import logging
from datetime import datetime, timedelta, timezone

from app.auth import get_password_hash
from app.config import SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD
from app.database import db
from app.models.schemas import DEFAULT_SEAT_CAPACITY

logger = logging.getLogger(__name__)

PASSWORD_FIELD = "hashed_password"

_DEMO_FLIGHTS = [
    ("Athens (ATH)", "London (LHR)", 5, "10:30", 185.50, "3h 45m"),
    ("Thessaloniki (SKG)", "Frankfurt (FRA)", 7, "14:15", 210.00, "2h 40m"),
    ("Athens (ATH)", "Paris (CDG)", 10, "08:45", 150.75, "3h 25m"),
    ("Athens (ATH)", "Rome (FCO)", 12, "19:05", 129.90, "2h 05m"),
    ("Thessaloniki (SKG)", "Munich (MUC)", 14, "06:20", 168.40, "2h 15m"),
]


async def _seed_admin() -> None:
    if not SEED_ADMIN_EMAIL or not SEED_ADMIN_PASSWORD:
        logger.warning(
            "SEED_ON_STARTUP is enabled but SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD "
            "are not both set — skipping administrator seeding."
        )
        return

    if await db.users.find_one({"email": SEED_ADMIN_EMAIL}):
        return

    await db.users.insert_one(
        {
            "fullname": "Administrator",
            "username": SEED_ADMIN_EMAIL,
            "email": SEED_ADMIN_EMAIL,
            PASSWORD_FIELD: get_password_hash(SEED_ADMIN_PASSWORD),
            "passport_num": "ADMIN001",
            "is_admin": True,
            "is_active": True,
        }
    )
    logger.info("Seeded administrator %s", SEED_ADMIN_EMAIL)


async def _seed_flights() -> None:
    if await db.availableFlights.count_documents({}):
        return

    today = datetime.now(timezone.utc)
    docs = []
    for departure, destination, offset, time, cost, duration in _DEMO_FLIGHTS:
        date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
        docs.append(
            {
                # Matches the designator the API generates, which the old
                # seed data did not — it used invented codes like "AEE123".
                "unique_code": (
                    f"{departure[-4:-1]}{destination[-4:-1]}"
                    f"{date.replace('-', '')[2:]}{time[:2]}"
                ),
                "departure": departure,
                "destination": destination,
                "date": date,
                "time": time,
                "cost": cost,
                "duration": duration,
                "availability": DEFAULT_SEAT_CAPACITY,
                "created_at": datetime.now(timezone.utc),
            }
        )

    await db.availableFlights.insert_many(docs)
    logger.info("Seeded %d demo flights", len(docs))


async def seed_data() -> None:
    await _seed_admin()
    await _seed_flights()
