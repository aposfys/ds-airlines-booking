from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_active_user
from app.db import get_session
from app.models.domain import (
    Booking,
    BookingStatus,
    FareClass,
    Flight,
    FlightSeat,
    FlightStatus,
    Route,
    SeatStatus,
    User,
)
from app.schemas import BookingCreate, BookingResponse, generate_booking_reference

router = APIRouter()

# A reference is six characters from a 32-symbol alphabet — about 10^9
# combinations. Collisions are vanishingly rare but not impossible, and the
# unique constraint will catch one, so retry rather than fail the sale.
_REFERENCE_ATTEMPTS = 5


def _to_response(booking: Booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        booking_reference=booking.booking_reference,
        status=booking.status.value,
        flight_number=booking.flight.flight_number,
        origin_iata=booking.flight.route.origin_iata,
        destination_iata=booking.flight.route.destination_iata,
        scheduled_departure=booking.flight.scheduled_departure,
        fare_class_code=booking.fare_class_code,
        passenger_full_name=booking.passenger_full_name,
        seat_numbers=sorted(s.seat_number for s in booking.seats),
        card_last4=booking.card_last4,
        amount_eur=booking.amount_eur,
        created_at=booking.created_at,
    )


def _booking_query():
    return select(Booking).options(
        selectinload(Booking.flight).selectinload(Flight.route).selectinload(Route.origin),
        selectinload(Booking.flight)
        .selectinload(Flight.route)
        .selectinload(Route.destination),
        selectinload(Booking.seats),
    )


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Sell a seat.

    This is the change ADR-001 was written for. The MongoDB version claimed
    the seat with an atomic decrement, inserted the booking, and undid the
    decrement by hand if the insert failed — a compensating write that leaked
    a seat permanently if the process died in between (DEF-007).

    Here the seat lock, the seat state change and the booking insert are one
    transaction, committed once by the session dependency. There is no
    interleaving in which a seat is consumed without a booking against it.
    """
    flight = await session.scalar(
        select(Flight)
        .options(selectinload(Flight.route))
        .where(Flight.id == payload.flight_id)
    )
    if flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    if flight.status is not FlightStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This flight is {flight.status.value} and cannot be booked",
        )

    fare_class = await session.get(FareClass, payload.fare_class_code)
    if fare_class is None:
        raise HTTPException(status_code=404, detail="Unknown fare class")

    # Lock the seat row. FOR UPDATE means a second request for the same seat
    # blocks here until this transaction resolves, rather than both reading
    # "available" and both proceeding.
    seat_query = (
        select(FlightSeat)
        .where(
            FlightSeat.flight_id == flight.id,
            FlightSeat.status == SeatStatus.AVAILABLE,
        )
        .order_by(FlightSeat.seat_number)
        .limit(1)
        .with_for_update(skip_locked=payload.seat_number is None)
    )
    if payload.seat_number:
        seat_query = seat_query.where(FlightSeat.seat_number == payload.seat_number)

    seat = await session.scalar(seat_query)
    if seat is None:
        detail = (
            f"Seat {payload.seat_number} is not available"
            if payload.seat_number
            else "This flight is full"
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    booking = Booking(
        user_id=current_user.id,
        flight_id=flight.id,
        fare_class_code=fare_class.code,
        passenger_full_name=payload.passenger_full_name,
        passenger_passport=payload.passenger_passport,
        card_last4=payload.card_last4,  # the full number is never persisted
        amount_eur=(flight.base_fare_eur * fare_class.price_multiplier).quantize(
            Decimal("0.01")
        ),
        status=BookingStatus.CONFIRMED,
    )

    for attempt in range(_REFERENCE_ATTEMPTS):
        booking.booking_reference = generate_booking_reference()
        session.add(booking)
        try:
            await session.flush()
            break
        except IntegrityError:
            await session.rollback()
            if attempt == _REFERENCE_ATTEMPTS - 1:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not allocate a booking reference",
                )

    seat.status = SeatStatus.BOOKED
    seat.booking_id = booking.id
    seat.held_until = None
    await session.flush()

    created = await session.scalar(_booking_query().where(Booking.id == booking.id))
    return _to_response(created)


@router.get("/", response_model=list[BookingResponse])
async def list_my_bookings(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    bookings = (
        await session.scalars(
            _booking_query()
            .where(Booking.user_id == current_user.id)
            .order_by(Booking.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).unique().all()
    return [_to_response(b) for b in bookings]


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a booking and return its seat to inventory.

    Ownership is part of the query, so another passenger's booking is a 404
    rather than a 403 — the existence of someone else's booking is not ours
    to confirm. The booking is marked cancelled rather than deleted: a sale
    that happened is a record the airline has to keep.
    """
    booking = await session.scalar(
        select(Booking)
        .options(selectinload(Booking.seats))
        .where(Booking.id == booking_id, Booking.user_id == current_user.id)
        .with_for_update()
    )
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Cancelling twice must not credit a second seat back to inventory.
    if booking.status is BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This booking is already cancelled"
        )

    for seat in booking.seats:
        seat.status = SeatStatus.AVAILABLE
        seat.booking_id = None
        seat.held_until = None

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)
    await session.flush()
