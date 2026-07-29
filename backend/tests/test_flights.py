import pytest

from app.models.schemas import FlightCreate
from app.routers.flights import _generate_flight_code, _station_code


class TestFlightCodeGeneration:
    """DEF-006 — codes were built from the first letter of each city name."""

    def test_uses_the_iata_code_when_present(self):
        assert _station_code("Athens (ATH)") == "ATH"
        assert _station_code("London (LHR)") == "LHR"

    def test_falls_back_to_the_city_name(self):
        assert _station_code("Chania") == "CHA"
        assert _station_code("Ios") == "IOS"

    def test_distinct_routes_do_not_collide(self):
        # Athens->Berlin and Amsterdam->Brussels both produced "AB..." before,
        # so creating the second flight failed as a duplicate.
        athens_berlin = _generate_flight_code(
            FlightCreate(
                departure="Athens (ATH)",
                destination="Berlin (BER)",
                date="2026-09-08",
                time="14:00",
                cost=120.0,
                duration="3h",
            )
        )
        amsterdam_brussels = _generate_flight_code(
            FlightCreate(
                departure="Amsterdam (AMS)",
                destination="Brussels (BRU)",
                date="2026-09-08",
                time="14:00",
                cost=120.0,
                duration="1h",
            )
        )
        assert athens_berlin != amsterdam_brussels


class TestFlightValidation:
    def test_rejects_a_route_to_itself(self):
        with pytest.raises(ValueError):
            FlightCreate(
                departure="Athens (ATH)",
                destination="Athens (ATH)",
                date="2026-09-08",
                time="14:00",
                cost=120.0,
                duration="3h",
            )

    def test_rejects_a_non_positive_fare(self):
        with pytest.raises(ValueError):
            FlightCreate(
                departure="Athens (ATH)",
                destination="Rome (FCO)",
                date="2026-09-08",
                time="14:00",
                cost=0,
                duration="2h",
            )

    def test_rejects_a_malformed_date(self):
        with pytest.raises(ValueError):
            FlightCreate(
                departure="Athens (ATH)",
                destination="Rome (FCO)",
                date="08/09/2026",
                time="14:00",
                cost=120.0,
                duration="2h",
            )


class TestSearch:
    async def test_search_is_open_to_anonymous_callers(self, client, flight):
        response = await client.get("/api/flights/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_filters_by_destination(self, client, flight):
        assert len((await client.get("/api/flights/?destination=London")).json()) == 1
        assert len((await client.get("/api/flights/?destination=Berlin")).json()) == 0

    async def test_regex_metacharacters_are_treated_literally(self, client, flight):
        """DEF-005 — search terms went into $regex unescaped.

        `.*` matched everything before the fix; a catastrophically
        backtracking pattern could pin a CPU core on an unauthenticated
        endpoint.
        """
        response = await client.get("/api/flights/?destination=.*")
        assert response.status_code == 200
        assert response.json() == []

    async def test_pagination_bounds_are_enforced(self, client, flight):
        assert (await client.get("/api/flights/?limit=0")).status_code == 422
        assert (await client.get("/api/flights/?limit=5000")).status_code == 422

    async def test_unknown_flight_returns_404(self, client, fake_db):
        assert (await client.get("/api/flights/NOSUCHCODE")).status_code == 404


class TestFlightDeletion:
    async def test_cannot_delete_a_flight_that_has_bookings(
        self, client, fake_db, flight, admin, auth_header
    ):
        await fake_db.bookings.insert_one(
            {"flight_code": flight["unique_code"], "user_id": "someone"}
        )
        headers = await auth_header(admin)
        response = await client.delete(
            f"/api/flights/{flight['unique_code']}", headers=headers
        )
        assert response.status_code == 409

    async def test_deletes_an_empty_flight(self, client, flight, admin, auth_header):
        headers = await auth_header(admin)
        response = await client.delete(
            f"/api/flights/{flight['unique_code']}", headers=headers
        )
        assert response.status_code == 204
