from sqlalchemy import func, select

from app.auth import get_password_hash, verify_password
from app.models.domain import User


class TestPasswordHashing:
    def test_hash_is_not_reversible_and_verifies(self):
        hashed = get_password_hash("securepassword1")
        assert hashed != "securepassword1"
        assert verify_password("securepassword1", hashed) is True
        assert verify_password("wrongpassword1", hashed) is False

    def test_verify_tolerates_a_malformed_stored_hash(self):
        assert verify_password("anything", "") is False
        assert verify_password("anything", "not-a-bcrypt-hash") is False


def _registration(**overrides) -> dict:
    payload = {
        "email": "new@example.com",
        "username": "newuser",
        "full_name": "New User",
        "passport_number": "AB123456",
        "password": "password123",
    }
    payload.update(overrides)
    return payload


class TestRegistration:
    async def test_creates_an_account(self, client):
        response = await client.post("/api/auth/register", json=_registration())
        assert response.status_code == 201, response.text
        assert response.json()["email"] == "new@example.com"

    async def test_never_stores_the_plaintext_password(self, client, session):
        await client.post("/api/auth/register", json=_registration())
        user = await session.scalar(select(User).where(User.username == "newuser"))
        assert user.hashed_password != "password123"
        assert verify_password("password123", user.hashed_password)

    async def test_response_never_exposes_the_hash(self, client):
        response = await client.post("/api/auth/register", json=_registration())
        assert "hashed_password" not in response.json()
        assert "password" not in response.json()

    async def test_privilege_cannot_be_self_assigned(self, client, session):
        await client.post("/api/auth/register", json=_registration(is_admin=True))
        user = await session.scalar(select(User).where(User.username == "newuser"))
        assert user.is_admin is False

    async def test_rejects_invalid_email(self, client):
        response = await client.post(
            "/api/auth/register", json=_registration(email="invalid-email")
        )
        assert response.status_code == 422

    async def test_rejects_password_without_a_digit(self, client):
        # The UI promised "8+ characters and a number"; the API enforced
        # neither (DEF-012).
        response = await client.post(
            "/api/auth/register", json=_registration(password="passwordonly")
        )
        assert response.status_code == 422

    async def test_rejects_password_without_a_letter(self, client):
        response = await client.post(
            "/api/auth/register", json=_registration(password="12345678")
        )
        assert response.status_code == 422

    async def test_rejects_duplicate_username(self, client, passenger):
        response = await client.post(
            "/api/auth/register",
            json=_registration(username="passenger", email="other@example.com"),
        )
        assert response.status_code == 409

    async def test_rejects_duplicate_email_differing_only_in_case(
        self, client, passenger
    ):
        """The Mongo unique index was case-sensitive, so Ada@x and ada@x were
        two accounts. The relational index is on lower(email)."""
        response = await client.post(
            "/api/auth/register",
            json=_registration(email="PASSENGER@example.com", username="other"),
        )
        assert response.status_code == 409


class TestLogin:
    async def test_returns_a_bearer_token(self, client, passenger):
        response = await client.post(
            "/api/auth/login", json={"username": "passenger", "password": "passenger123"}
        )
        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"]

    async def test_rejects_a_wrong_password(self, client, passenger):
        response = await client.post(
            "/api/auth/login", json={"username": "passenger", "password": "wrongpassword1"}
        )
        assert response.status_code == 401

    async def test_rejects_an_unknown_user(self, client):
        response = await client.post(
            "/api/auth/login", json={"username": "ghost", "password": "whatever123"}
        )
        assert response.status_code == 401

    async def test_error_does_not_reveal_whether_the_user_exists(self, client, passenger):
        unknown = await client.post(
            "/api/auth/login", json={"username": "ghost", "password": "whatever123"}
        )
        wrong = await client.post(
            "/api/auth/login", json={"username": "passenger", "password": "wrongpassword1"}
        )
        assert unknown.json()["detail"] == wrong.json()["detail"]

    async def test_deactivated_account_cannot_log_in(self, client, session, passenger):
        passenger.is_active = False
        await session.flush()
        response = await client.post(
            "/api/auth/login", json={"username": "passenger", "password": "passenger123"}
        )
        assert response.status_code == 403


class TestAdminCreatedAccounts:
    async def test_an_admin_created_account_can_log_in(self, client, admin_header):
        """DEF-008 — this handler wrote `hashed_password` while login read
        `password`, so accounts it created returned 500 at login forever."""
        created = await client.post(
            "/api/admin/admins",
            headers=admin_header,
            json={
                "email": "second.ops@dsairlines.example",
                "username": "ops2",
                "full_name": "Second Administrator",
                "passport_number": "CD987654",
                "password": "password123",
            },
        )
        assert created.status_code == 201, created.text

        login = await client.post(
            "/api/auth/login", json={"username": "ops2", "password": "password123"}
        )
        assert login.status_code == 200, login.text

        token = login.json()["access_token"]
        dashboard = await client.get(
            "/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"}
        )
        assert dashboard.status_code == 200


class TestCurrentUser:
    async def test_me_returns_the_real_profile(self, client, passenger_header):
        # The frontend used to invent this from the JWT (DEF-016).
        response = await client.get("/api/auth/me", headers=passenger_header)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Test Passenger"
        assert response.json()["email"] == "passenger@example.com"
