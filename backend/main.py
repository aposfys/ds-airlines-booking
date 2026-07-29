import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import SEED_ON_STARTUP
from app.database import client, ensure_indexes
from app.routers import admin, auth, bookings, flights
from app.seed import seed_data

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # @app.on_event has been deprecated since FastAPI 0.93 and emits a
    # DeprecationWarning on every startup.
    try:
        await client.server_info()
        logger.info("Connected to MongoDB")
        await ensure_indexes()
        if SEED_ON_STARTUP:
            await seed_data()
    except Exception:
        # Startup continues so that /health can report the failure, rather
        # than the container crash-looping with the reason buried in logs.
        logger.exception("Database initialisation failed")

    yield

    client.close()


app = FastAPI(
    title="DS Airlines API",
    description="Backend API for DS Airlines, a modern flight booking system.",
    version="2.0.0",
    lifespan=lifespan,
)

# In development, any localhost port is acceptable. In production the allowed
# origins must be listed explicitly — the previous regex permitted localhost
# only, which silently breaks any real deployment.
_allowed_origins = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
]
if _allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
        await client.server_info()
        return {"status": "ok", "database": "up"}
    except Exception:
        return {"status": "degraded", "database": "down"}
