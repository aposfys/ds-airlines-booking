"""Booking domain tests.

The whole of this surface was unreachable by the original suite, which is why
the seat leak (DEF-007) and the cleartext card storage (DEF-003) survived.
"""

from sqlalchemy import func, select

from app.models.domain import Booking, BookingStatus, FlightSeat, SeatStatus

A_REAL_LOOKING_CARD = "4242424242424242"


def _payload(flight_id, **overrides) -> dict:
    body = {
        "flight_id": str(flight_id),
        "fare_class_code": "LIGHT",
        "passenger_full_name": "Test Passenger",
        "passenger_passport": "AB123456",
    }
    body.update(overrides)
    return body


async def _available(session, flight_id) -> int:
    return await session.scalar(
        select(func.count())
        .select_from(FlightSeat)
        .where(FlightSeat.flight_id == flight_id, FlightSeat.status == SeatStatus.AVAILABLE)
    )


class TestCardHandling:
    """DEF-003, resolved in full.

    Phase 0 stopped storing the PAN. Phase 1 stops accepting one: this is a
    public demonstration with no payment provider, and an ordinary-looking
    card field will eventually be given a real card.
    """

    async def test_a_booking_needs_no_payment_details(
        self, client, flight, passenger_header
    ):
        response = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        assert response.status_code == 201, response.text

    async def test_a_card_number_is_refused_rather_than_ignored(
        self, client, flight, passenger_header
    ):
        """The important half. Silently dropping an unexpected `credit_card`
        would let a client keep posting live PANs to a server that merely
        chose not to read them."""
        response = await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json=_payload(flight.id, credit_card=A_REAL_LOOKING_CARD),
        )
        assert response.status_code == 422

    async def test_no_card_data_reaches_the_database(
        self, client, session, flight, passenger_header
    ):
        await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        booking = await session.scalar(select(Booking))
        assert booking.card_last4 is None

        row = {c.name: str(getattr(booking, c.name)) for c in Booking.__table__.columns}
        assert A_REAL_LOOKING_CARD not in " ".join(row.values())

    async def test_response_carries_no_card_field_value(
        self, client, flight, passenger_header
    ):
        response = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        assert response.json()["card_last4"] is None
        assert A_REAL_LOOKING_CARD not in response.text


class TestBookingReference:
    async def test_reference_is_six_unambiguous_characters(
        self, client, flight, passenger_header
    ):
        response = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        reference = response.json()["booking_reference"]
        assert len(reference) == 6
        # I, O, 0 and 1 are excluded: a reference gets read aloud and written down.
        assert not set(reference) & set("IO01")

    async def test_references_are_unique_across_bookings(
        self, client, flight, passenger_header
    ):
        references = set()
        for _ in range(5):
            response = await client.post(
                "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
            )
            references.add(response.json()["booking_reference"])
        assert len(references) == 5


class TestSeatInventory:
    async def test_booking_consumes_exactly_one_seat(
        self, client, session, flight, passenger_header
    ):
        before = await _available(session, flight.id)
        response = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        assert response.status_code == 201
        assert await _available(session, flight.id) == before - 1

    async def test_booked_seat_is_linked_to_its_booking(
        self, client, session, flight, passenger_header
    ):
        response = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        seat_number = response.json()["seat_numbers"][0]

        seat = await session.scalar(
            select(FlightSeat).where(
                FlightSeat.flight_id == flight.id, FlightSeat.seat_number == seat_number
            )
        )
        assert seat.status is SeatStatus.BOOKED
        # The check constraint makes the alternative unrepresentable.
        assert seat.booking_id is not None

    async def test_a_specific_seat_can_be_requested(
        self, client, flight, passenger_header
    ):
        response = await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json=_payload(flight.id, seat_number="12A"),
        )
        assert response.status_code == 201, response.text
        assert response.json()["seat_numbers"] == ["12A"]

    async def test_an_already_taken_seat_is_refused(
        self, client, flight, passenger_header
    ):
        await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json=_payload(flight.id, seat_number="12A"),
        )
        second = await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json=_payload(flight.id, seat_number="12A"),
        )
        assert second.status_code == 409

    async def test_a_full_flight_is_refused(
        self, client, session, flight, passenger_header
    ):
        # Hold every seat rather than marking them BOOKED: the check
        # constraint requires a booked seat to name its booking, so there is
        # no way to fake a sold cabin without sales. Holding is the honest
        # equivalent and leaves nothing AVAILABLE.
        from datetime import datetime, timedelta, timezone

        await session.execute(
            FlightSeat.__table__.update()
            .where(FlightSeat.flight_id == flight.id)
            .values(
                status=SeatStatus.HELD,
                held_until=datetime.now(timezone.utc) + timedelta(minutes=10),
            )
        )
        await session.flush()

        response = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        assert response.status_code == 409

    async def test_unknown_flight_is_refused(self, client, passenger_header):
        import uuid

        response = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(uuid.uuid4())
        )
        assert response.status_code == 404

    async def test_unknown_fare_class_is_refused(
        self, client, flight, passenger_header
    ):
        response = await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json=_payload(flight.id, fare_class_code="GOLD"),
        )
        assert response.status_code == 404


class TestFarePricing:
    async def test_amount_charged_follows_the_fare_class_multiplier(
        self, client, flight, passenger_header
    ):
        light = await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json=_payload(flight.id, fare_class_code="LIGHT"),
        )
        flex = await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json=_payload(flight.id, fare_class_code="FLEX"),
        )
        # base 129.00; LIGHT x1.00, FLEX x2.10
        assert light.json()["amount_eur"] == "129.00"
        assert flex.json()["amount_eur"] == "270.90"


class TestCancellation:
    async def test_cancelling_returns_the_seat(
        self, client, session, flight, passenger_header
    ):
        before = await _available(session, flight.id)
        created = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        booking_id = created.json()["id"]

        response = await client.delete(
            f"/api/bookings/{booking_id}", headers=passenger_header
        )
        assert response.status_code == 204
        assert await _available(session, flight.id) == before

    async def test_cancelling_marks_rather_than_deletes(
        self, client, session, flight, passenger_header
    ):
        created = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        await client.delete(
            f"/api/bookings/{created.json()['id']}", headers=passenger_header
        )

        booking = await session.scalar(select(Booking))
        # A sale that happened is a record the airline has to keep.
        assert booking is not None
        assert booking.status is BookingStatus.CANCELLED
        assert booking.cancelled_at is not None

    async def test_cancelling_twice_cannot_credit_a_second_seat(
        self, client, session, flight, passenger_header
    ):
        before = await _available(session, flight.id)
        created = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        booking_id = created.json()["id"]

        first = await client.delete(f"/api/bookings/{booking_id}", headers=passenger_header)
        second = await client.delete(f"/api/bookings/{booking_id}", headers=passenger_header)

        assert first.status_code == 204
        assert second.status_code == 409
        assert await _available(session, flight.id) == before


class TestOwnership:
    async def test_bookings_are_scoped_to_the_caller(
        self, client, flight, passenger_header, admin_header
    ):
        await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        response = await client.get("/api/bookings/", headers=admin_header)
        assert response.status_code == 200
        assert response.json() == []

    async def test_cannot_cancel_another_passengers_booking(
        self, client, flight, passenger_header, admin_header
    ):
        created = await client.post(
            "/api/bookings/", headers=passenger_header, json=_payload(flight.id)
        )
        response = await client.delete(
            f"/api/bookings/{created.json()['id']}", headers=admin_header
        )
        # 404, not 403 — another passenger's booking is not ours to confirm.
        assert response.status_code == 404

    async def test_booking_requires_authentication(self, client, flight):
        response = await client.post("/api/bookings/", json=_payload(flight.id))
        assert response.status_code == 401
