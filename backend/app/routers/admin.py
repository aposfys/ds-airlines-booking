from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_admin, get_password_hash
from app.db import get_session
from app.models.domain import Booking, BookingStatus, Flight, FlightSeat, SeatStatus, User
from app.schemas import UserCreate, UserResponse

router = APIRouter()


@router.get("/dashboard")
async def dashboard(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """Operational summary.

    Reachable at all only because DEF-001 is fixed; before Phase 0 every
    caller received 403 here, administrators included.

    These are joins and aggregates — the queries ADR-001 cites as a reason to
    be relational. Phase 4 builds the full ops surface on them.
    """
    scheduled_flights = await session.scalar(
        select(func.count()).select_from(Flight)
    )
    confirmed_bookings = await session.scalar(
        select(func.count())
        .select_from(Booking)
        .where(Booking.status == BookingStatus.CONFIRMED)
    )
    revenue = await session.scalar(
        select(func.coalesce(func.sum(Booking.amount_eur), 0)).where(
            Booking.status == BookingStatus.CONFIRMED
        )
    )
    seats_sold = await session.scalar(
        select(func.count())
        .select_from(FlightSeat)
        .where(FlightSeat.status == SeatStatus.BOOKED)
    )
    seats_total = await session.scalar(select(func.count()).select_from(FlightSeat))

    return {
        "administrator": current_user.full_name,
        "flights": scheduled_flights,
        "confirmed_bookings": confirmed_bookings,
        "revenue_eur": float(revenue or 0),
        "seats_sold": seats_sold,
        "load_factor": round((seats_sold or 0) / seats_total, 4) if seats_total else 0.0,
    }


@router.post("/admins", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
):
    """Promote a new administrator.

    This handler used to write the digest to `hashed_password` while login
    read `password`, so every account it created raised a KeyError at login
    and returned 500 permanently (DEF-008). Both now go through the same
    mapped column, which is a class of bug the schema no longer permits.
    """
    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        passport_number=payload.passport_number,
        hashed_password=get_password_hash(payload.password),
        is_admin=True,
        is_active=True,
    )
    session.add(user)

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered",
        )

    return user
