"""The DS Airlines relational domain model.

Replaces the three MongoDB collections (`users`, `availableFlights`,
`bookings`) with a schema that expresses what an airline actually sells.

Rationale for the migration is in docs/adr/0001-postgresql-over-mongodb.md.
The short version: booking has to be one transaction, the data is a graph of
foreign keys, and integrity belongs in the database rather than in whichever
code paths remembered to check.

Constraints here are deliberate and load-bearing. Each one closes a defect
that the document model could only address by convention — see the comments
against DEF-* identifiers, which refer to
docs/analysis/current-state-assessment.md.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Interval,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── Reference data ────────────────────────────────────────


class Airport(Base):
    """A station. Keyed by IATA code because that is the real-world key.

    The document model had no airports at all — it stored the free-text
    string "Athens (ATH)" on every flight, which is why flight designators
    were built by slicing city names (DEF-006).
    """

    __tablename__ = "airports"

    iata_code: Mapped[str] = mapped_column(String(3), primary_key=True)
    icao_code: Mapped[str | None] = mapped_column(String(4), unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)  # IANA

    __table_args__ = (
        CheckConstraint("iata_code = upper(iata_code)", name="ck_airport_iata_upper"),
        CheckConstraint("char_length(iata_code) = 3", name="ck_airport_iata_len"),
    )

    def __repr__(self) -> str:
        return f"<Airport {self.iata_code}>"


class AircraftType(Base):
    """An equipment type. Seat capacity lives here, not on the flight.

    `DEFAULT_SEAT_CAPACITY = 220` was a module constant applied to every
    flight regardless of aircraft. Single-fleet today; the schema does not
    assume it stays that way.
    """

    __tablename__ = "aircraft_types"

    id: Mapped[uuid.UUID] = _uuid_pk()
    iata_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    seat_capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    aircraft: Mapped[list[Aircraft]] = relationship(back_populates="aircraft_type")
    seat_map: Mapped[list[SeatMapEntry]] = relationship(
        back_populates="aircraft_type", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("seat_capacity > 0", name="ck_aircraft_type_capacity_positive"),
    )


class Aircraft(Base):
    """A specific airframe, identified by registration."""

    __tablename__ = "aircraft"

    id: Mapped[uuid.UUID] = _uuid_pk()
    registration: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    aircraft_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("aircraft_types.id", ondelete="RESTRICT"), nullable=False
    )

    aircraft_type: Mapped[AircraftType] = relationship(back_populates="aircraft")
    flights: Mapped[list[Flight]] = relationship(back_populates="aircraft")


class SeatMapEntry(Base):
    """One physical seat in a cabin layout, per aircraft type.

    The layout belongs to the type; per-flight occupancy belongs to
    FlightSeat. Modelling it once per type rather than once per flight means
    a cabin reconfiguration is one change, not one per scheduled departure.
    """

    __tablename__ = "seat_map_entries"

    id: Mapped[uuid.UUID] = _uuid_pk()
    aircraft_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("aircraft_types.id", ondelete="CASCADE"), nullable=False
    )
    seat_number: Mapped[str] = mapped_column(String(4), nullable=False)  # "12A"
    row: Mapped[int] = mapped_column(Integer, nullable=False)
    column: Mapped[str] = mapped_column(String(1), nullable=False)
    is_window: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_aisle: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_exit_row: Mapped[bool] = mapped_column(nullable=False, default=False)

    aircraft_type: Mapped[AircraftType] = relationship(back_populates="seat_map")

    __table_args__ = (
        UniqueConstraint("aircraft_type_id", "seat_number", name="uq_seat_map_seat"),
        CheckConstraint("row > 0", name="ck_seat_map_row_positive"),
        # A seat cannot be both against the window and against the aisle.
        CheckConstraint(
            "NOT (is_window AND is_aisle)", name="ck_seat_map_window_xor_aisle"
        ),
    )


class Route(Base):
    """An origin-destination pair the airline is authorised to fly."""

    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = _uuid_pk()
    origin_iata: Mapped[str] = mapped_column(
        ForeignKey("airports.iata_code", ondelete="RESTRICT"), nullable=False
    )
    destination_iata: Mapped[str] = mapped_column(
        ForeignKey("airports.iata_code", ondelete="RESTRICT"), nullable=False
    )
    distance_km: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_duration: Mapped[timedelta] = mapped_column(Interval, nullable=False)

    origin: Mapped[Airport] = relationship(foreign_keys=[origin_iata])
    destination: Mapped[Airport] = relationship(foreign_keys=[destination_iata])
    flights: Mapped[list[Flight]] = relationship(back_populates="route")

    __table_args__ = (
        UniqueConstraint("origin_iata", "destination_iata", name="uq_route_od"),
        # The API validated this in Pydantic only; now nothing can write it.
        CheckConstraint(
            "origin_iata <> destination_iata", name="ck_route_origin_ne_destination"
        ),
        CheckConstraint("distance_km > 0", name="ck_route_distance_positive"),
    )


class FareClass(Base):
    """A branded fare and the rules attached to it.

    The document model had a single `cost` per flight and no concept of what
    that fare entitled the passenger to. The brand promises "cabin bag
    included, in every fare" — that promise now lives in data.
    """

    __tablename__ = "fare_classes"

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    price_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    cabin_bag_included: Mapped[bool] = mapped_column(nullable=False, default=True)
    checked_bag_included: Mapped[bool] = mapped_column(nullable=False, default=False)
    seat_selection_included: Mapped[bool] = mapped_column(nullable=False, default=False)
    changeable: Mapped[bool] = mapped_column(nullable=False, default=False)
    refundable: Mapped[bool] = mapped_column(nullable=False, default=False)
    change_fee_eur: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("price_multiplier > 0", name="ck_fare_class_multiplier_positive"),
        CheckConstraint("change_fee_eur >= 0", name="ck_fare_class_change_fee_non_neg"),
        # A refundable fare that cannot be changed is not a product we sell.
        CheckConstraint(
            "NOT refundable OR changeable", name="ck_fare_class_refundable_implies_change"
        ),
    )


# ── Operations ────────────────────────────────────────────


class FlightStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    DEPARTED = "departed"
    CANCELLED = "cancelled"


class Flight(Base, TimestampMixin):
    """A single dated leg — what a passenger actually books."""

    __tablename__ = "flights"

    id: Mapped[uuid.UUID] = _uuid_pk()
    flight_number: Mapped[str] = mapped_column(String(7), nullable=False)  # "DS1042"
    route_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False
    )
    aircraft_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("aircraft.id", ondelete="RESTRICT"), nullable=False
    )
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_departure: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scheduled_arrival: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    base_fare_eur: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[FlightStatus] = mapped_column(
        Enum(FlightStatus, name="flight_status", native_enum=True),
        nullable=False,
        default=FlightStatus.SCHEDULED,
    )

    route: Mapped[Route] = relationship(back_populates="flights")
    aircraft: Mapped[Aircraft] = relationship(back_populates="flights")
    seats: Mapped[list[FlightSeat]] = relationship(
        back_populates="flight", cascade="all, delete-orphan"
    )
    bookings: Mapped[list[Booking]] = relationship(back_populates="flight")

    __table_args__ = (
        # Replaces the generated designator that collided by construction
        # (DEF-006). A flight number is unique per operating day, which is how
        # airlines actually identify a leg.
        UniqueConstraint("flight_number", "departure_date", name="uq_flight_number_date"),
        CheckConstraint("base_fare_eur > 0", name="ck_flight_fare_positive"),
        CheckConstraint(
            "scheduled_arrival > scheduled_departure", name="ck_flight_arrival_after_dep"
        ),
        Index("ix_flight_route_date", "route_id", "departure_date"),
        Index("ix_flight_departure_date", "departure_date"),
    )


class SeatStatus(enum.StrEnum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"


class FlightSeat(Base):
    """Occupancy of one seat on one flight.

    This replaces `availability: int` — a bare counter that could drift out of
    step with reality and did (DEF-007). Inventory is now the count of rows in
    a state, so a seat cannot be lost without a row being wrong, and a booking
    holds a foreign key to the specific seat it occupies.

    `held_until` supports Phase 2 seat holds without a second datastore; see
    ADR-001 on why Redis was deferred.
    """

    __tablename__ = "flight_seats"

    id: Mapped[uuid.UUID] = _uuid_pk()
    flight_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("flights.id", ondelete="CASCADE"), nullable=False
    )
    seat_number: Mapped[str] = mapped_column(String(4), nullable=False)
    status: Mapped[SeatStatus] = mapped_column(
        Enum(SeatStatus, name="seat_status", native_enum=True),
        nullable=False,
        default=SeatStatus.AVAILABLE,
    )
    held_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL")
    )

    flight: Mapped[Flight] = relationship(back_populates="seats")
    booking: Mapped[Booking | None] = relationship(back_populates="seats")

    __table_args__ = (
        UniqueConstraint("flight_id", "seat_number", name="uq_flight_seat"),
        # A booked seat must name its booking, and only a booked seat may.
        CheckConstraint(
            "(status = 'BOOKED') = (booking_id IS NOT NULL)",
            name="ck_flight_seat_booked_has_booking",
        ),
        # A held seat must say when the hold lapses, or it is held forever.
        CheckConstraint(
            "(status = 'HELD') = (held_until IS NOT NULL)",
            name="ck_flight_seat_held_has_expiry",
        ),
        Index("ix_flight_seat_flight_status", "flight_id", "status"),
    )


# ── People and sales ──────────────────────────────────────


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    username: Mapped[str] = mapped_column(String(32), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    passport_number: Mapped[str | None] = mapped_column(String(20))
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_admin: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    bookings: Mapped[list[Booking]] = relationship(back_populates="user")

    __table_args__ = (
        # Case-insensitive uniqueness. The Mongo index was case-sensitive, so
        # Ada@x.com and ada@x.com were two accounts (a refinement on DEF-013).
        Index("uq_user_email_lower", func.lower(email), unique=True),
        Index("uq_user_username_lower", func.lower(username), unique=True),
    )


class BookingStatus(enum.StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(Base, TimestampMixin):
    """A sale.

    Denormalised copies of the route, date and fare are gone: the document
    version duplicated `cost`, `departure`, `destination` and `flight_date`
    off the flight with nothing keeping them in step. `amount_eur` is the
    exception and is kept deliberately — it is what the passenger was
    actually charged, which must not change if the fare is later repriced.
    """

    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = _uuid_pk()
    booking_reference: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    flight_id: Mapped[uuid.UUID] = mapped_column(
        # RESTRICT is the point: deleting a flight that has bookings is now
        # impossible at the database level, not merely checked (DEF-019).
        ForeignKey("flights.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fare_class_code: Mapped[str] = mapped_column(
        ForeignKey("fare_classes.code", ondelete="RESTRICT"), nullable=False
    )

    passenger_full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    passenger_passport: Mapped[str] = mapped_column(String(20), nullable=False)

    # Nullable, and null for every booking this application creates.
    #
    # Phase 0 stopped *storing* the full card number (DEF-003). Phase 1 stops
    # accepting one: this is a public demonstration with no payment provider
    # behind it, and a field that looks like a normal card input will
    # eventually be given a real card by someone who did not read the page.
    # The safest cardholder data is the kind that never reaches the process.
    #
    # The column is kept so that a real payment integration has somewhere to
    # put the last four digits it is given back by the provider.
    card_last4: Mapped[str | None] = mapped_column(String(4))

    amount_eur: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status", native_enum=True),
        nullable=False,
        default=BookingStatus.CONFIRMED,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="bookings")
    flight: Mapped[Flight] = relationship(back_populates="bookings")
    fare_class: Mapped[FareClass] = relationship()
    seats: Mapped[list[FlightSeat]] = relationship(back_populates="booking")

    __table_args__ = (
        CheckConstraint("amount_eur >= 0", name="ck_booking_amount_non_negative"),
        CheckConstraint(
            "card_last4 IS NULL OR card_last4 ~ '^[0-9]{4}$'",
            name="ck_booking_card_last4_digits",
        ),
        CheckConstraint(
            "booking_reference ~ '^[A-Z0-9]{6}$'", name="ck_booking_reference_format"
        ),
        # A cancelled booking records when; a live one must not.
        CheckConstraint(
            "(status = 'CANCELLED') = (cancelled_at IS NOT NULL)",
            name="ck_booking_cancelled_has_timestamp",
        ),
        Index("ix_booking_user", "user_id"),
        Index("ix_booking_flight", "flight_id"),
    )
