from datetime import date, timedelta


def _flight_payload(**overrides) -> dict:
    payload = {
        "flight_number": "DS2402",
        "origin_iata": "ATH",
        "destination_iata": "FCO",
        "departure_date": str(date.today() + timedelta(days=21)),
        "departure_time": "19:05",
        "aircraft_registration": "SX-DLB",
        "base_fare_eur": "89.00",
    }
    payload.update(overrides)
    return payload


class TestSearch:
    async def test_search_is_open_to_anonymous_callers(self, client, flight):
        response = await client.get("/api/flights/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_filters_by_origin_and_destination(self, client, flight):
        assert len((await client.get("/api/flights/?origin=ATH")).json()) == 1
        assert len((await client.get("/api/flights/?origin=SKG")).json()) == 0
        assert len((await client.get("/api/flights/?destination=LHR")).json()) == 1
        assert len((await client.get("/api/flights/?destination=FRA")).json()) == 0

    async def test_iata_codes_are_matched_case_insensitively(self, client, flight):
        assert len((await client.get("/api/flights/?origin=ath")).json()) == 1

    async def test_regex_metacharacters_have_no_special_meaning(self, client, flight):
        """DEF-005 — search terms went into a Mongo $regex unescaped.

        There is no pattern matching left for that bug to live in: origin and
        destination are exact matches against the airports table. `.*` is
        simply not an IATA code.
        """
        response = await client.get("/api/flights/?origin=.*")
        assert response.status_code == 200
        assert response.json() == []

    async def test_pagination_bounds_are_enforced(self, client, flight):
        assert (await client.get("/api/flights/?limit=0")).status_code == 422
        assert (await client.get("/api/flights/?limit=5000")).status_code == 422

    async def test_unknown_flight_returns_404(self, client):
        import uuid

        assert (await client.get(f"/api/flights/{uuid.uuid4()}")).status_code == 404

    async def test_search_returns_a_price_per_fare_class(self, client, flight):
        fares = (await client.get("/api/flights/")).json()[0]["fares"]
        assert [f["fare_class_code"] for f in fares] == ["LIGHT", "STANDARD", "FLEX"]
        # base 129.00 x 1.00 / 1.45 / 2.10
        assert [f["price_eur"] for f in fares] == ["129.00", "187.05", "270.90"]

    async def test_fare_rules_are_carried_in_the_response(self, client, flight):
        fares = {f["fare_class_code"]: f for f in (await client.get("/api/flights/")).json()[0]["fares"]}
        # The brand promises a cabin bag in every fare.
        assert all(f["cabin_bag_included"] for f in fares.values())
        assert fares["LIGHT"]["refundable"] is False
        assert fares["FLEX"]["refundable"] is True


class TestFlightCreation:
    async def test_creates_a_flight_and_materialises_the_cabin(
        self, client, admin_header, reference_data
    ):
        response = await client.post(
            "/api/flights/", headers=admin_header, json=_flight_payload()
        )
        assert response.status_code == 201, response.text
        assert response.json()["seats_available"] == 220

    async def test_same_number_on_the_same_day_is_refused(
        self, client, admin_header, reference_data
    ):
        first = await client.post(
            "/api/flights/", headers=admin_header, json=_flight_payload()
        )
        assert first.status_code == 201
        second = await client.post(
            "/api/flights/", headers=admin_header, json=_flight_payload()
        )
        assert second.status_code == 409

    async def test_same_number_on_a_different_day_is_allowed(
        self, client, admin_header, reference_data
    ):
        await client.post("/api/flights/", headers=admin_header, json=_flight_payload())
        response = await client.post(
            "/api/flights/",
            headers=admin_header,
            json=_flight_payload(
                departure_date=str(date.today() + timedelta(days=22))
            ),
        )
        assert response.status_code == 201, response.text

    async def test_distinct_routes_do_not_collide(
        self, client, admin_header, reference_data
    ):
        """DEF-006 — designators were built from the first letter of each city,
        so Athens->Berlin and Amsterdam->Brussels produced the same code. A
        flight number unique per operating day cannot collide that way."""
        first = await client.post(
            "/api/flights/", headers=admin_header, json=_flight_payload()
        )
        second = await client.post(
            "/api/flights/",
            headers=admin_header,
            json=_flight_payload(
                flight_number="DS2660", destination_iata="BCN", departure_time="13:20"
            ),
        )
        assert first.status_code == 201
        assert second.status_code == 201, second.text

    async def test_unknown_route_is_refused(self, client, admin_header, reference_data):
        response = await client.post(
            "/api/flights/",
            headers=admin_header,
            json=_flight_payload(origin_iata="BCN", destination_iata="MUC"),
        )
        assert response.status_code == 404

    async def test_unknown_aircraft_is_refused(
        self, client, admin_header, reference_data
    ):
        response = await client.post(
            "/api/flights/",
            headers=admin_header,
            json=_flight_payload(aircraft_registration="SX-ZZZ"),
        )
        assert response.status_code == 404

    async def test_malformed_flight_number_is_refused(
        self, client, admin_header, reference_data
    ):
        response = await client.post(
            "/api/flights/", headers=admin_header, json=_flight_payload(flight_number="XX1")
        )
        assert response.status_code == 422

    async def test_non_positive_fare_is_refused(
        self, client, admin_header, reference_data
    ):
        response = await client.post(
            "/api/flights/", headers=admin_header, json=_flight_payload(base_fare_eur="0")
        )
        assert response.status_code == 422

    async def test_arrival_is_derived_from_the_route_duration(
        self, client, admin_header, reference_data
    ):
        response = await client.post(
            "/api/flights/", headers=admin_header, json=_flight_payload()
        )
        # ATH-FCO is 125 minutes in the seeded route table.
        assert response.json()["duration_minutes"] == 125


class TestRepricing:
    async def test_an_empty_flight_can_be_repriced(self, client, admin_header, flight):
        response = await client.patch(
            f"/api/flights/{flight.id}",
            headers=admin_header,
            json={"base_fare_eur": "99.00"},
        )
        assert response.status_code == 200
        assert response.json()["fares"][0]["price_eur"] == "99.00"

    async def test_a_flight_with_bookings_cannot_be_repriced(
        self, client, admin_header, passenger_header, flight
    ):
        await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json={
                "flight_id": str(flight.id),
                "fare_class_code": "LIGHT",
                "passenger_full_name": "Test Passenger",
                "passenger_passport": "AB123456",
            },
        )
        response = await client.patch(
            f"/api/flights/{flight.id}",
            headers=admin_header,
            json={"base_fare_eur": "99.00"},
        )
        assert response.status_code == 409

    async def test_a_passenger_cannot_reprice(self, client, passenger_header, flight):
        response = await client.patch(
            f"/api/flights/{flight.id}",
            headers=passenger_header,
            json={"base_fare_eur": "1.00"},
        )
        assert response.status_code == 403


class TestDeletion:
    async def test_an_empty_flight_can_be_deleted(self, client, admin_header, flight):
        response = await client.delete(
            f"/api/flights/{flight.id}", headers=admin_header
        )
        assert response.status_code == 204

    async def test_a_flight_with_bookings_cannot_be_deleted(
        self, client, admin_header, passenger_header, flight
    ):
        """DEF-019 — deleting a flight orphaned its bookings.

        bookings.flight_id is ON DELETE RESTRICT, so the database refuses this
        rather than a handler remembering to count first.
        """
        await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json={
                "flight_id": str(flight.id),
                "fare_class_code": "LIGHT",
                "passenger_full_name": "Test Passenger",
                "passenger_passport": "AB123456",
            },
        )
        response = await client.delete(f"/api/flights/{flight.id}", headers=admin_header)
        assert response.status_code == 409

    async def test_cancelled_flights_are_excluded_from_search(
        self, client, admin_header, flight
    ):
        await client.patch(
            f"/api/flights/{flight.id}", headers=admin_header, json={"status": "cancelled"}
        )
        assert (await client.get("/api/flights/")).json() == []

    async def test_a_cancelled_flight_cannot_be_booked(
        self, client, admin_header, passenger_header, flight
    ):
        await client.patch(
            f"/api/flights/{flight.id}", headers=admin_header, json={"status": "cancelled"}
        )
        response = await client.post(
            "/api/bookings/",
            headers=passenger_header,
            json={
                "flight_id": str(flight.id),
                "fare_class_code": "LIGHT",
                "passenger_full_name": "Test Passenger",
                "passenger_passport": "AB123456",
            },
        )
        assert response.status_code == 409
