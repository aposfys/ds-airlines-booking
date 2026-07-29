from motor.motor_asyncio import AsyncIOMotorClient

from app.config import DB_NAME, MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


async def ensure_indexes() -> None:
    """Create the indexes the query patterns depend on.

    Without these, uniqueness was enforced only by a read-then-write check in
    the register handler, which two concurrent requests can both pass, and
    every flight search was a full collection scan.
    """
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.availableFlights.create_index("unique_code", unique=True)
    await db.availableFlights.create_index(
        [("departure", 1), ("destination", 1), ("date", 1)]
    )
    await db.bookings.create_index("user_id")
    await db.bookings.create_index("flight_code")


async def get_db():
    return db
