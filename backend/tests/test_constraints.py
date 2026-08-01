"""Database-level integrity tests.

These are the tests the Phase 0 fake could not express. Its limitation was
stated plainly at the time: passing tests were evidence about our own logic,
not about the database. Every case here bypasses the API entirely and asserts
that PostgreSQL itself refuses to store nonsense — so the guarantee holds for
migrations, admin scripts and any future service, not only for the code paths
that remembered to check.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.domain import (
    Airport,
    Booking,
    BookingStatus,
    FareClass,
    FlightSeat,
    Route,
    SeatMapEntry,
    SeatStatus,
)


async def _expect_violation(session, obj, constraint_fragment: str):
    session.add(obj)
    with pytest.raises(IntegrityError) as excinfo:
        await session.flush()
    assert constraint_fragment in str(excinfo.value)
    await session.rollback()


class TestRouteConstraints:
    async def test_a_route_cannot_end_where_it_starts(self, session, reference_data):
        await _expect_violation(
            session,
            Route(
                origin_iata="ATH",
                destination_iata="ATH",
                distance_km=1,
                scheduled_duration=timedelta(hours=1),
            ),
            "ck_route_origin_ne_destination",
        )

    async def test_distance_must_be_positive(self, session, reference_data):
        await _expect_violation(
            session,
            Route(
                origin_iata="ATH",
                destination_iata="MUC",
                distance_km=-5,
                scheduled_duration=timedelta(hours=2),
            ),
            "ck_route_distance_positive",
        )

    async def test_a_route_pair_is_unique(self, session, reference_data):
        await _expect_violation(
            session,
            Route(
                origin_iata="ATH",
                destination_iata="LHR",
                distance_km=2395,
                scheduled_duration=timedelta(minutes=225),
            ),
            "uq_route_od",
        )


class TestAirportConstraints:
    async def test_iata_code_must_be_uppercase(self, session):
        await _expect_violation(
            session,
            Airport(
                iata_code="ath",
                name="Lowercase",
                city="Athens",
                country="GR",
                timezone="Europe/Athens",
            ),
            "ck_airport_iata_upper",
        )


class TestSeatConstraints:
    async def test_a_booked_seat_must_name_its_booking(self, session, flight):
        seat = await session.scalar(
            select(FlightSeat).where(FlightSeat.flight_id == flight.id).limit(1)
        )
        seat.status = SeatStatus.BOOKED
        seat.booking_id = None
        with pytest.raises(IntegrityError) as excinfo:
            await session.flush()
        assert "ck_flight_seat_booked_has_booking" in str(excinfo.value)
        await session.rollback()

    async def test_a_held_seat_must_name_its_expiry(self, session, flight):
        seat = await session.scalar(
            select(FlightSeat).where(FlightSeat.flight_id == flight.id).limit(1)
        )
        seat.status = SeatStatus.HELD
        seat.held_until = None
        with pytest.raises(IntegrityError) as excinfo:
            await session.flush()
        assert "ck_flight_seat_held_has_expiry" in str(excinfo.value)
        await session.rollback()

    async def test_a_seat_number_is_unique_per_flight(self, session, flight):
        await _expect_violation(
            session,
            FlightSeat(flight_id=flight.id, seat_number="1A"),
            "uq_flight_seat",
        )

    async def test_a_seat_cannot_be_both_window_and_aisle(self, session, reference_data):
        from app.models.domain import AircraftType

        aircraft_type = await session.scalar(select(AircraftType))
        await _expect_violation(
            session,
            SeatMapEntry(
                aircraft_type_id=aircraft_type.id,
                seat_number="99Z",
                row=99,
                column="Z",
                is_window=True,
                is_aisle=True,
            ),
            "ck_seat_map_window_xor_aisle",
        )


class TestFareClassConstraints:
    async def test_a_refundable_fare_must_also_be_changeable(self, session):
        await _expect_violation(
            session,
            FareClass(
                code="BROKEN",
                name="Broken",
                description="Refundable but not changeable",
                price_multiplier=Decimal("1.00"),
                changeable=False,
                refundable=True,
                sort_order=9,
            ),
            "ck_fare_class_refundable_implies_change",
        )

    async def test_the_price_multiplier_must_be_positive(self, session):
        await _expect_violation(
            session,
            FareClass(
                code="FREE",
                name="Free",
                description="Zero multiplier",
                price_multiplier=Decimal("0.00"),
                sort_order=9,
            ),
            "ck_fare_class_multiplier_positive",
        )


class TestBookingConstraints:
    async def _booking(self, flight, **overrides) -> Booking:
        booking = Booking(
            booking_reference="ABC234",
            user_id=overrides.pop("user_id"),
            flight_id=flight.id,
            fare_class_code="LIGHT",
            passenger_full_name="Test Passenger",
            passenger_passport="AB123456",
            card_last4="4242",
            amount_eur=Decimal("129.00"),
            status=BookingStatus.CONFIRMED,
        )
        for key, value in overrides.items():
            setattr(booking, key, value)
        return booking

    async def test_card_last4_must_be_four_digits(self, session, flight, passenger):
        await _expect_violation(
            session,
            await self._booking(flight, user_id=passenger.id, card_last4="42a4"),
            "ck_booking_card_last4_digits",
        )

    async def test_reference_must_match_the_expected_format(
        self, session, flight, passenger
    ):
        await _expect_violation(
            session,
            await self._booking(flight, user_id=passenger.id, booking_reference="abc-12"),
            "ck_booking_reference_format",
        )

    async def test_a_cancelled_booking_must_record_when(
        self, session, flight, passenger
    ):
        await _expect_violation(
            session,
            await self._booking(
                flight,
                user_id=passenger.id,
                status=BookingStatus.CANCELLED,
                cancelled_at=None,
            ),
            "ck_booking_cancelled_has_timestamp",
        )

    async def test_a_live_booking_must_not_record_a_cancellation_time(
        self, session, flight, passenger
    ):
        await _expect_violation(
            session,
            await self._booking(
                flight,
                user_id=passenger.id,
                status=BookingStatus.CONFIRMED,
                cancelled_at=datetime.now(timezone.utc),
            ),
            "ck_booking_cancelled_has_timestamp",
        )

    async def test_a_booking_reference_is_unique(self, session, flight, passenger):
        session.add(await self._booking(flight, user_id=passenger.id))
        await session.flush()
        await _expect_violation(
            session,
            await self._booking(flight, user_id=passenger.id),
            "bookings_booking_reference_key",
        )

    async def test_a_booking_cannot_reference_a_missing_flight(
        self, session, passenger, reference_data
    ):
        # reference_data is required: without the fare classes seeded, the
        # fare_class_code FK fires first and this asserts the wrong constraint.
        booking = Booking(
            booking_reference="ABC235",
            user_id=passenger.id,
            flight_id=uuid.uuid4(),
            fare_class_code="LIGHT",
            passenger_full_name="Test Passenger",
            passenger_passport="AB123456",
            card_last4="4242",
            amount_eur=Decimal("129.00"),
        )
        await _expect_violation(session, booking, "bookings_flight_id_fkey")
