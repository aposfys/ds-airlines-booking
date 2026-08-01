"""Reference and demo data.

Seeding is opt-in (SEED_ON_STARTUP) and has no default credentials. It used
to run unconditionally on every startup, production included, creating an
administrator with the password `admin` hardcoded in this file (DEF-004).

Reference data — airports, aircraft, seat maps, routes, fare classes — is
seeded whenever it is missing, because the application cannot sell anything
without it. Demo flights and the administrator are gated behind the flag.
"""

import logging
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_password_hash
from app.config import SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD
from app.models.domain import (
    Aircraft,
    AircraftType,
    Airport,
    FareClass,
    Flight,
    FlightSeat,
    Route,
    SeatMapEntry,
    User,
)

logger = logging.getLogger(__name__)

A321NEO_CAPACITY = 220
_CABIN_COLUMNS = "ABCDEF"
_EXIT_ROWS = {12, 13}

_AIRPORTS = [
    ("ATH", "LGAV", "Athens International Eleftherios Venizelos", "Athens", "GR", "Europe/Athens"),
    ("SKG", "LGTS", "Thessaloniki Makedonia", "Thessaloniki", "GR", "Europe/Athens"),
    ("LHR", "EGLL", "London Heathrow", "London", "GB", "Europe/London"),
    ("CDG", "LFPG", "Paris Charles de Gaulle", "Paris", "FR", "Europe/Paris"),
    ("FRA", "EDDF", "Frankfurt am Main", "Frankfurt", "DE", "Europe/Berlin"),
    ("MUC", "EDDM", "Munich Franz Josef Strauss", "Munich", "DE", "Europe/Berlin"),
    ("FCO", "LIRF", "Rome Fiumicino", "Rome", "IT", "Europe/Rome"),
    ("BCN", "LEBL", "Barcelona El Prat", "Barcelona", "ES", "Europe/Madrid"),
]

# (origin, destination, distance_km, minutes)
_ROUTES = [
    ("ATH", "LHR", 2395, 225),
    ("ATH", "CDG", 2100, 205),
    ("ATH", "FCO", 1050, 125),
    ("ATH", "BCN", 1900, 190),
    ("ATH", "MUC", 1500, 155),
    ("SKG", "FRA", 1650, 160),
    ("SKG", "MUC", 1350, 145),
]

_FARE_CLASSES = [
    # code, name, description, multiplier, cabin, checked, seat, change, refund, fee, order
    ("LIGHT", "Light", "Cabin bag included. Seat assigned at check-in.",
     Decimal("1.00"), True, False, False, False, False, Decimal("0.00"), 1),
    ("STANDARD", "Standard", "Cabin bag, checked bag and seat selection included.",
     Decimal("1.45"), True, True, True, True, False, Decimal("35.00"), 2),
    ("FLEX", "Flex", "Fully changeable and refundable, with everything in Standard.",
     Decimal("2.10"), True, True, True, True, True, Decimal("0.00"), 3),
]

_DEMO_FLIGHTS = [
    ("DS1040", "ATH", "LHR", 5, "10:30", Decimal("129.00")),
    ("DS1042", "ATH", "LHR", 6, "18:15", Decimal("149.00")),
    ("DS2210", "ATH", "CDG", 7, "08:45", Decimal("119.00")),
    ("DS2402", "ATH", "FCO", 4, "19:05", Decimal("89.00")),
    ("DS2660", "ATH", "BCN", 9, "13:20", Decimal("139.00")),
    ("DS3120", "SKG", "FRA", 6, "14:15", Decimal("155.00")),
    ("DS3140", "SKG", "MUC", 8, "06:20", Decimal("132.00")),
]


def _a321neo_seat_map() -> list[tuple[str, int, str, bool, bool, bool]]:
    """220 seats, six abreast. Returns (number, row, column, window, aisle, exit)."""
    seats: list[tuple[str, int, str, bool, bool, bool]] = []
    row = 1
    while len(seats) < A321NEO_CAPACITY:
        for column in _CABIN_COLUMNS:
            if len(seats) == A321NEO_CAPACITY:
                break
            seats.append(
                (
                    f"{row}{column}",
                    row,
                    column,
                    column in ("A", "F"),
                    column in ("C", "D"),
                    row in _EXIT_ROWS,
                )
            )
        row += 1
    return seats


async def _seed_reference_data(session: AsyncSession) -> None:
    if await session.scalar(select(func.count()).select_from(Airport)):
        return

    logger.info("Seeding reference data")
    session.add_all(
        Airport(
            iata_code=iata, icao_code=icao, name=name, city=city, country=cc, timezone=tz
        )
        for iata, icao, name, city, cc, tz in _AIRPORTS
    )

    aircraft_type = AircraftType(
        iata_code="32Q", name="Airbus A321neo", seat_capacity=A321NEO_CAPACITY
    )
    session.add(aircraft_type)
    await session.flush()

    session.add_all(
        SeatMapEntry(
            aircraft_type_id=aircraft_type.id,
            seat_number=number,
            row=row,
            column=column,
            is_window=window,
            is_aisle=aisle,
            is_exit_row=exit_row,
        )
        for number, row, column, window, aisle, exit_row in _a321neo_seat_map()
    )

    # Single-fleet, as the brand book describes.
    session.add_all(
        Aircraft(registration=reg, aircraft_type_id=aircraft_type.id)
        for reg in ("SX-DLA", "SX-DLB", "SX-DLC", "SX-DLD", "SX-DLE")
    )

    session.add_all(
        Route(
            origin_iata=origin,
            destination_iata=destination,
            distance_km=distance,
            scheduled_duration=timedelta(minutes=minutes),
        )
        for origin, destination, distance, minutes in _ROUTES
    )

    session.add_all(
        FareClass(
            code=code,
            name=name,
            description=description,
            price_multiplier=multiplier,
            cabin_bag_included=cabin,
            checked_bag_included=checked,
            seat_selection_included=seat,
            changeable=change,
            refundable=refund,
            change_fee_eur=fee,
            sort_order=order,
        )
        for code, name, description, multiplier, cabin, checked, seat, change, refund, fee, order in _FARE_CLASSES
    )
    await session.flush()


async def _seed_admin(session: AsyncSession) -> None:
    if not SEED_ADMIN_EMAIL or not SEED_ADMIN_PASSWORD:
        logger.warning(
            "SEED_ON_STARTUP is enabled but SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD "
            "are not both set — skipping administrator seeding."
        )
        return

    exists = await session.scalar(
        select(User).where(func.lower(User.email) == SEED_ADMIN_EMAIL.lower())
    )
    if exists:
        return

    session.add(
        User(
            email=SEED_ADMIN_EMAIL,
            username=SEED_ADMIN_EMAIL.split("@")[0],
            full_name="Operations Administrator",
            passport_number=None,
            hashed_password=get_password_hash(SEED_ADMIN_PASSWORD),
            is_admin=True,
            is_active=True,
        )
    )
    await session.flush()
    logger.info("Seeded administrator %s", SEED_ADMIN_EMAIL)


async def _seed_flights(session: AsyncSession) -> None:
    if await session.scalar(select(func.count()).select_from(Flight)):
        return

    aircraft = list((await session.scalars(select(Aircraft))).all())
    if not aircraft:
        return

    seat_map = list(
        (
            await session.scalars(
                select(SeatMapEntry).where(
                    SeatMapEntry.aircraft_type_id == aircraft[0].aircraft_type_id
                )
            )
        ).all()
    )

    today = date.today()
    for index, (number, origin, destination, offset, dep, fare) in enumerate(_DEMO_FLIGHTS):
        route = await session.scalar(
            select(Route).where(
                Route.origin_iata == origin, Route.destination_iata == destination
            )
        )
        if route is None:
            continue

        hour, minute = (int(p) for p in dep.split(":"))
        departure = datetime.combine(
            today + timedelta(days=offset), time(hour, minute), tzinfo=timezone.utc
        )
        flight = Flight(
            flight_number=number,
            route_id=route.id,
            aircraft_id=aircraft[index % len(aircraft)].id,
            departure_date=departure.date(),
            scheduled_departure=departure,
            scheduled_arrival=departure + route.scheduled_duration,
            base_fare_eur=fare,
        )
        session.add(flight)
        await session.flush()

        session.add_all(
            FlightSeat(flight_id=flight.id, seat_number=s.seat_number) for s in seat_map
        )

    await session.flush()
    logger.info("Seeded %d demo flights", len(_DEMO_FLIGHTS))


async def seed_data(session: AsyncSession) -> None:
    await _seed_reference_data(session)
    await _seed_admin(session)
    await _seed_flights(session)
