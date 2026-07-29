"""Booking domain tests.

None of this was covered before: the entire flights/bookings surface was
untested, which is why the seat leak and the cleartext card storage were
never surfaced.
"""

VALID_CARD = "4242424242424242"  # passes Luhn


def _booking_payload(flight_code: str, **overrides) -> dict:
    payload = {
        "flight_code": flight_code,
        "full_name": "Test Passenger",
        "passport_num": "AB123456",
        "credit_card": VALID_CARD,
    }
    payload.update(overrides)
    return payload


class TestCardHandling:
    """DEF-003 — full PAN persisted in cleartext next to a passport number."""

    async def test_full_card_number_is_never_persisted(
        self, client, fake_db, flight, passenger, auth_header
    ):
        headers = await auth_header(passenger)
        response = await client.post(
            "/api/bookings/", headers=headers, json=_booking_payload(flight["unique_code"])
        )
        assert response.status_code == 201, response.text

        stored = await fake_db.bookings.find_one({"flight_code": flight["unique_code"]})
        assert "credit_card" not in stored
        assert VALID_CARD not in str(stored)
        assert stored["card_last4"] == "4242"

    async def test_response_does_not_echo_the_card(
        self, client, flight, passenger, auth_header
    ):
        headers = await auth_header(passenger)
        response = await client.post(
            "/api/bookings/", headers=headers, json=_booking_payload(flight["unique_code"])
        )
        assert VALID_CARD not in response.text

    async def test_rejects_a_card_failing_the_luhn_checksum(
        self, client, flight, passenger, auth_header
    ):
        headers = await auth_header(passenger)
        response = await client.post(
            "/api/bookings/",
            headers=headers,
            json=_booking_payload(flight["unique_code"], credit_card="4242424242424243"),
        )
        assert response.status_code == 422


class TestSeatInventory:
    async def test_booking_decrements_availability(
        self, client, fake_db, flight, passenger, auth_header
    ):
        headers = await auth_header(passenger)
        await client.post(
            "/api/bookings/", headers=headers, json=_booking_payload(flight["unique_code"])
        )
        updated = await fake_db.availableFlights.find_one(
            {"unique_code": flight["unique_code"]}
        )
        assert updated["availability"] == flight["availability"] - 1

    async def test_full_flight_is_rejected(
        self, client, fake_db, flight, passenger, auth_header
    ):
        await fake_db.availableFlights.update_one(
            {"unique_code": flight["unique_code"]}, {"$set": {"availability": 0}}
        )
        headers = await auth_header(passenger)
        response = await client.post(
            "/api/bookings/", headers=headers, json=_booking_payload(flight["unique_code"])
        )
        assert response.status_code == 409

    async def test_cancelling_returns_the_seat(
        self, client, fake_db, flight, passenger, auth_header
    ):
        headers = await auth_header(passenger)
        created = await client.post(
            "/api/bookings/", headers=headers, json=_booking_payload(flight["unique_code"])
        )
        booking_id = created.json()["_id"]

        response = await client.delete(f"/api/bookings/{booking_id}", headers=headers)
        assert response.status_code == 204

        updated = await fake_db.availableFlights.find_one(
            {"unique_code": flight["unique_code"]}
        )
        assert updated["availability"] == flight["availability"]

    async def test_unknown_flight_is_rejected(self, client, fake_db, passenger, auth_header):
        headers = await auth_header(passenger)
        response = await client.post(
            "/api/bookings/", headers=headers, json=_booking_payload("NOSUCHFLIGHT")
        )
        assert response.status_code == 404


class TestBookingOwnership:
    async def test_bookings_are_scoped_to_the_caller(
        self, client, fake_db, flight, passenger, admin, auth_header
    ):
        passenger_headers = await auth_header(passenger)
        await client.post(
            "/api/bookings/",
            headers=passenger_headers,
            json=_booking_payload(flight["unique_code"]),
        )

        admin_headers = await auth_header(admin)
        response = await client.get("/api/bookings/", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_cannot_cancel_another_users_booking(
        self, client, fake_db, flight, passenger, admin, auth_header
    ):
        passenger_headers = await auth_header(passenger)
        created = await client.post(
            "/api/bookings/",
            headers=passenger_headers,
            json=_booking_payload(flight["unique_code"]),
        )
        booking_id = created.json()["_id"]

        admin_headers = await auth_header(admin)
        response = await client.delete(f"/api/bookings/{booking_id}", headers=admin_headers)
        assert response.status_code == 404

    async def test_cancelling_twice_is_rejected(
        self, client, fake_db, flight, passenger, auth_header
    ):
        headers = await auth_header(passenger)
        created = await client.post(
            "/api/bookings/", headers=headers, json=_booking_payload(flight["unique_code"])
        )
        booking_id = created.json()["_id"]

        assert (await client.delete(f"/api/bookings/{booking_id}", headers=headers)).status_code == 204
        # A second cancellation must not credit another seat back.
        assert (await client.delete(f"/api/bookings/{booking_id}", headers=headers)).status_code == 404

        updated = await fake_db.availableFlights.find_one(
            {"unique_code": flight["unique_code"]}
        )
        assert updated["availability"] == flight["availability"]

    async def test_booking_requires_authentication(self, client, fake_db, flight):
        response = await client.post(
            "/api/bookings/", json=_booking_payload(flight["unique_code"])
        )
        assert response.status_code == 401
