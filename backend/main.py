import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import SEED_ON_STARTUP
from app.db import SessionFactory, engine
from app.routers import admin, auth, bookings, flights
from app.seed import seed_data

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema creation is Alembic's job, not the application's. `alembic
    # upgrade head` runs before the app starts — see the Dockerfile entrypoint.
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("Connected to PostgreSQL")

        if SEED_ON_STARTUP:
            async with SessionFactory() as session:
                await seed_data(session)
                await session.commit()
    except Exception:
        # Startup continues so /health can report the failure, rather than the
        # container crash-looping with the reason buried in logs.
        logger.exception("Database initialisation failed")

    yield

    await engine.dispose()


app = FastAPI(
    title="DS Airlines API",
    description=(
        "Booking API for DS Airlines, a Greek short-haul carrier."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# In development any localhost port is acceptable. In production the allowed
# origins must be listed explicitly via CORS_ORIGINS — the localhost-only
# regex silently breaks any real deployment.
_allowed_origins = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    **(
        {"allow_origins": _allowed_origins}
        if _allowed_origins
        else {"allow_origin_regex": r"https?://(localhost|127\.0\.0\.1)(:\d+)?"}
    ),
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(flights.router, prefix="/api/flights", tags=["Flights"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
async def root():
    return {"message": "Welcome to DS Airlines API"}


@app.get("/health")
async def health_check():
    """Liveness and database reachability, used by the compose healthcheck."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "up"}
    except Exception:
        return {"status": "degraded", "database": "down"}
