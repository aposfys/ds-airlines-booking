from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_admin
from app.db import get_session
from app.models.domain import (
    Aircraft,
    Airport,
    FareClass,
    Flight,
    FlightSeat,
    FlightStatus,
    Route,
    SeatMapEntry,
    SeatStatus,
    User,
)
from app.schemas import FareOption, FlightCreate, FlightSummary, FlightUpdate

router = APIRouter()


async def _seats_available(session: AsyncSession, flight_id: UUID) -> int:
    return (
        await session.scalar(
            select(func.count())
            .select_from(FlightSeat)
            .where(
                FlightSeat.flight_id == flight_id,
                FlightSeat.status == SeatStatus.AVAILABLE,
            )
        )
        or 0
    )


async def _to_summary(
    session: AsyncSession, flight: Flight, fare_classes: list[FareClass]
) -> FlightSummary:
    available = await _seats_available(session, flight.id)
    duration = flight.scheduled_arrival - flight.scheduled_departure

    return FlightSummary(
        id=flight.id,
        flight_number=flight.flight_number,
        origin_iata=flight.route.origin_iata,
        origin_city=flight.route.origin.city,
        destination_iata=flight.route.destination_iata,
        destination_city=flight.route.destination.city,
        departure_date=flight.departure_date,
        scheduled_departure=flight.scheduled_departure,
        scheduled_arrival=flight.scheduled_arrival,
        duration_minutes=int(duration.total_seconds() // 60),
        aircraft_type=flight.aircraft.aircraft_type.name,
        seats_available=available,
        fares=[
            FareOption(
                fare_class_code=fc.code,
                name=fc.name,
                # The branded fare is derived from the flight's base fare, so
                # repricing a flight moves every fare with it rather than
                # leaving classes inconsistent.
                price_eur=(flight.base_fare_eur * fc.price_multiplier).quantize(
                    Decimal("0.01")
                ),
                seats_available=available,
                cabin_bag_included=fc.cabin_bag_included,
                checked_bag_included=fc.checked_bag_included,
                changeable=fc.changeable,
                refundable=fc.refundable,
            )
            for fc in fare_classes
        ],
    )


def _flight_query():
    return select(Flight).options(
        selectinload(Flight.route).selectinload(Route.origin),
        selectinload(Flight.route).selectinload(Route.destination),
        selectinload(Flight.aircraft).selectinload(Aircraft.aircraft_type),
    )


@router.get("/", response_model=list[FlightSummary])
async def search_flights(
    origin: str | None = Query(default=None, max_length=3),
    destination: str | None = Query(default=None, max_length=3),
    departure_date: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Search scheduled flights.

    Origin and destination are IATA codes matched exactly against the
    airports table. The previous implementation interpolated free text into a
    MongoDB $regex, which allowed collection probing and catastrophic
    backtracking from an unauthenticated endpoint (DEF-005). There is no
    pattern matching here for that class of bug to live in.
    """
    query = _flight_query().where(Flight.status == FlightStatus.SCHEDULED)

    if origin:
        query = query.join(Flight.route).where(Route.origin_iata == origin.upper())
    if destination:
        query = query.where(
            Flight.route_id.in_(
                select(Route.id).where(Route.destination_iata == destination.upper())
            )
        )
    if departure_date:
        query = query.where(Flight.departure_date == departure_date)

    query = query.order_by(Flight.scheduled_departure).limit(limit).offset(offset)
    flights = (await session.scalars(query)).unique().all()

    fare_classes = list(
        (await session.scalars(select(FareClass).order_by(FareClass.sort_order))).all()
    )
    return [await _to_summary(session, f, fare_classes) for f in flights]


@router.get("/{flight_id}", response_model=FlightSummary)
async def get_flight(flight_id: UUID, session: AsyncSession = Depends(get_session)):
    flight = await session.scalar(_flight_query().where(Flight.id == flight_id))
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    fare_classes = list(
        (await session.scalars(select(FareClass).order_by(FareClass.sort_order))).all()
    )
    return await _to_summary(session, flight, fare_classes)


@router.post("/", response_model=FlightSummary, status_code=status.HTTP_201_CREATED)
async def create_flight(
    payload: FlightCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
):
    route = await session.scalar(
        select(Route).where(
            Route.origin_iata == payload.origin_iata,
            Route.destination_iata == payload.destination_iata,
        )
    )
    if route is None:
        raise HTTPException(
            status_code=404,
            detail=f"No route {payload.origin_iata}–{payload.destination_iata} exists",
        )

    aircraft = await session.scalar(
        select(Aircraft)
        .options(selectinload(Aircraft.aircraft_type))
        .where(Aircraft.registration == payload.aircraft_registration)
    )
    if aircraft is None:
        raise HTTPException(status_code=404, detail="Aircraft not found")

    hour, minute = (int(p) for p in payload.departure_time.split(":"))
    departure = datetime.combine(
        payload.departure_date, time(hour, minute), tzinfo=timezone.utc
    )

    flight = Flight(
        flight_number=payload.flight_number,
        route_id=route.id,
        aircraft_id=aircraft.id,
        departure_date=payload.departure_date,
        scheduled_departure=departure,
        scheduled_arrival=departure + route.scheduled_duration,
        base_fare_eur=payload.base_fare_eur,
        status=FlightStatus.SCHEDULED,
    )
    session.add(flight)

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That flight number already operates on that date",
        )

    # Materialise the cabin. Inventory is rows, not a counter, so every seat
    # the aircraft has must exist before the flight can be sold.
    seat_map = (
        await session.scalars(
            select(SeatMapEntry).where(
                SeatMapEntry.aircraft_type_id == aircraft.aircraft_type_id
            )
        )
    ).all()
    if not seat_map:
        raise HTTPException(
            status_code=422,
            detail=f"No seat map defined for aircraft type {aircraft.aircraft_type.name}",
        )
    session.add_all(
        FlightSeat(flight_id=flight.id, seat_number=s.seat_number) for s in seat_map
    )
    await session.flush()

    created = await session.scalar(_flight_query().where(Flight.id == flight.id))
    fare_classes = list(
        (await session.scalars(select(FareClass).order_by(FareClass.sort_order))).all()
    )
    return await _to_summary(session, created, fare_classes)


@router.patch("/{flight_id}", response_model=FlightSummary)
async def update_flight(
    flight_id: UUID,
    payload: FlightUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
):
    flight = await session.scalar(_flight_query().where(Flight.id == flight_id))
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    if payload.base_fare_eur is not None:
        sold = await session.scalar(
            select(func.count())
            .select_from(FlightSeat)
            .where(
                FlightSeat.flight_id == flight_id,
                FlightSeat.status == SeatStatus.BOOKED,
            )
        )
        # Repricing a flight that already carries passengers would leave those
        # bookings holding a fare that no longer exists. What they paid is
        # recorded on the booking, but the flight's advertised fare must not
        # drift away from it silently.
        if sold:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot reprice a flight with {sold} booked seat(s)",
            )
        flight.base_fare_eur = payload.base_fare_eur

    if payload.status is not None:
        try:
            flight.status = FlightStatus(payload.status)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"status must be one of {[s.value for s in FlightStatus]}",
            )

    await session.flush()
    fare_classes = list(
        (await session.scalars(select(FareClass).order_by(FareClass.sort_order))).all()
    )
    return await _to_summary(session, flight, fare_classes)


@router.delete("/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flight(
    flight_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
):
    flight = await session.get(Flight, flight_id)
    if flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")

    try:
        await session.delete(flight)
        await session.flush()
    except IntegrityError:
        await session.rollback()
        # bookings.flight_id is ON DELETE RESTRICT, so this is refused by the
        # database rather than by a count check that could race (DEF-019).
        # Cancelling the flight is the correct operation; deletion is not.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a flight that has bookings — cancel it instead",
        )
