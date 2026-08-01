"""Regression tests for DEF-001 and DEF-002.

Before Phase 0, tokens carried only `sub` and `exp` while every check read
`is_admin` off the payload, so these endpoints returned 403 to every caller
including administrators. No test existed that would have caught it.
"""


class TestAdminAccess:
    async def test_admin_can_reach_dashboard(self, client, admin_header):
        response = await client.get("/api/admin/dashboard", headers=admin_header)
        assert response.status_code == 200

    async def test_passenger_cannot_reach_dashboard(self, client, passenger_header):
        response = await client.get("/api/admin/dashboard", headers=passenger_header)
        assert response.status_code == 403

    async def test_anonymous_cannot_reach_dashboard(self, client):
        assert (await client.get("/api/admin/dashboard")).status_code == 401

    async def test_admin_can_create_a_flight(
        self, client, admin_header, reference_data
    ):
        from datetime import date, timedelta

        response = await client.post(
            "/api/flights/",
            headers=admin_header,
            json={
                "flight_number": "DS2402",
                "origin_iata": "ATH",
                "destination_iata": "FCO",
                "departure_date": str(date.today() + timedelta(days=21)),
                "departure_time": "19:05",
                "aircraft_registration": "SX-DLB",
                "base_fare_eur": "89.00",
            },
        )
        assert response.status_code == 201, response.text
        # The cabin must be materialised, or the flight cannot be sold.
        assert response.json()["seats_available"] == 220

    async def test_passenger_cannot_create_a_flight(
        self, client, passenger_header, reference_data
    ):
        from datetime import date, timedelta

        response = await client.post(
            "/api/flights/",
            headers=passenger_header,
            json={
                "flight_number": "DS2402",
                "origin_iata": "ATH",
                "destination_iata": "FCO",
                "departure_date": str(date.today() + timedelta(days=21)),
                "departure_time": "19:05",
                "aircraft_registration": "SX-DLB",
                "base_fare_eur": "89.00",
            },
        )
        assert response.status_code == 403

    async def test_passenger_cannot_create_an_admin(self, client, passenger_header):
        response = await client.post(
            "/api/admin/admins",
            headers=passenger_header,
            json={
                "email": "escalate@example.com",
                "username": "escalate",
                "full_name": "Escalation Attempt",
                "passport_number": "ZZ999999",
                "password": "password123",
            },
        )
        assert response.status_code == 403


class TestPrivilegeComesFromTheDatabase:
    """DEF-002 — the token was treated as the user record."""

    async def test_revoking_admin_takes_effect_before_expiry(
        self, client, session, admin, admin_header
    ):
        assert (
            await client.get("/api/admin/dashboard", headers=admin_header)
        ).status_code == 200

        admin.is_admin = False
        await session.flush()

        # Same still-valid token; privilege is read from the row.
        assert (
            await client.get("/api/admin/dashboard", headers=admin_header)
        ).status_code == 403

    async def test_deactivated_account_loses_access(
        self, client, session, passenger, passenger_header
    ):
        assert (await client.get("/api/auth/me", headers=passenger_header)).status_code == 200

        passenger.is_active = False
        await session.flush()

        assert (await client.get("/api/auth/me", headers=passenger_header)).status_code == 403

    async def test_deleted_account_loses_access(
        self, client, session, passenger, passenger_header
    ):
        await session.delete(passenger)
        await session.flush()
        assert (await client.get("/api/auth/me", headers=passenger_header)).status_code == 401

    async def test_garbage_token_is_rejected(self, client):
        response = await client.get(
            "/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
        )
        assert response.status_code == 401
