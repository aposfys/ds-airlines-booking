"""Regression tests for DEF-001 — the unreachable admin surface.

Before the fix, `create_access_token` emitted only `sub` and `exp`, while
every authorisation check read `is_admin` off the decoded payload. The key
was never present, so these endpoints returned 403 to every caller including
administrators. No test existed that would have caught it.
"""

import pytest


class TestAdminAccess:
    async def test_admin_can_reach_dashboard(self, client, admin, auth_header):
        headers = await auth_header(admin)
        response = await client.get("/api/admin/dashboard", headers=headers)
        assert response.status_code == 200

    async def test_passenger_cannot_reach_dashboard(self, client, passenger, auth_header):
        headers = await auth_header(passenger)
        response = await client.get("/api/admin/dashboard", headers=headers)
        assert response.status_code == 403

    async def test_anonymous_cannot_reach_dashboard(self, client):
        response = await client.get("/api/admin/dashboard")
        assert response.status_code == 401

    async def test_admin_can_create_flight(self, client, admin, auth_header):
        headers = await auth_header(admin)
        response = await client.post(
            "/api/flights/",
            headers=headers,
            json={
                "departure": "Athens (ATH)",
                "destination": "Rome (FCO)",
                "date": "2026-09-01",
                "time": "19:05",
                "cost": 129.90,
                "duration": "2h 05m",
            },
        )
        assert response.status_code == 201, response.text

    async def test_passenger_cannot_create_flight(self, client, passenger, auth_header):
        headers = await auth_header(passenger)
        response = await client.post(
            "/api/flights/",
            headers=headers,
            json={
                "departure": "Athens (ATH)",
                "destination": "Rome (FCO)",
                "date": "2026-09-01",
                "time": "19:05",
                "cost": 129.90,
                "duration": "2h 05m",
            },
        )
        assert response.status_code == 403


class TestPrivilegeIsReadFromTheDatabase:
    """DEF-002 — the token was treated as the user record."""

    async def test_revoking_admin_takes_effect_before_token_expiry(
        self, client, fake_db, admin, auth_header
    ):
        headers = await auth_header(admin)
        assert (await client.get("/api/admin/dashboard", headers=headers)).status_code == 200

        await fake_db.users.update_one(
            {"username": "ops"}, {"$set": {"is_admin": False}}
        )

        # Same, still-valid token — privileges must come from the record.
        assert (await client.get("/api/admin/dashboard", headers=headers)).status_code == 403

    async def test_deactivated_account_loses_access(
        self, client, fake_db, passenger, auth_header
    ):
        headers = await auth_header(passenger)
        assert (await client.get("/api/auth/me", headers=headers)).status_code == 200

        await fake_db.users.update_one(
            {"username": "passenger"}, {"$set": {"is_active": False}}
        )

        assert (await client.get("/api/auth/me", headers=headers)).status_code == 403

    async def test_deleted_account_loses_access(
        self, client, fake_db, passenger, auth_header
    ):
        headers = await auth_header(passenger)
        await fake_db.users.delete_one({"username": "passenger"})
        assert (await client.get("/api/auth/me", headers=headers)).status_code == 401

    async def test_garbage_token_is_rejected(self, client, fake_db):
        response = await client.get(
            "/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
        )
        assert response.status_code == 401
