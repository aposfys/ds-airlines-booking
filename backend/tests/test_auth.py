from app.auth import get_password_hash, verify_password
from app.routers.auth import PASSWORD_FIELD


class TestPasswordHashing:
    def test_hash_is_not_reversible_and_verifies(self):
        hashed = get_password_hash("securepassword1")
        assert hashed != "securepassword1"
        assert verify_password("securepassword1", hashed) is True
        assert verify_password("wrongpassword1", hashed) is False

    def test_verify_tolerates_a_malformed_stored_hash(self):
        # A record written by an older schema version must not raise.
        assert verify_password("anything", "") is False
        assert verify_password("anything", "not-a-bcrypt-hash") is False


class TestRegistration:
    async def test_creates_an_account(self, client, fake_db):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "username": "newuser",
                "fullname": "New User",
                "password": "password123",
                "passport_num": "AB123456",
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["email"] == "new@example.com"

    async def test_never_stores_the_plaintext_password(self, client, fake_db):
        await client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "username": "newuser",
                "fullname": "New User",
                "password": "password123",
                "passport_num": "AB123456",
            },
        )
        stored = await fake_db.users.find_one({"username": "newuser"})
        assert "password" not in stored
        assert stored[PASSWORD_FIELD] != "password123"
        assert verify_password("password123", stored[PASSWORD_FIELD])

    async def test_response_never_exposes_the_hash(self, client, fake_db):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "username": "newuser",
                "fullname": "New User",
                "password": "password123",
                "passport_num": "AB123456",
            },
        )
        assert PASSWORD_FIELD not in response.json()
        assert "password" not in response.json()

    async def test_privilege_cannot_be_self_assigned(self, client, fake_db):
        # is_admin is not part of UserCreate; sending it must not take effect.
        await client.post(
            "/api/auth/register",
            json={
                "email": "sneaky@example.com",
                "username": "sneaky",
                "fullname": "Sneaky User",
                "password": "password123",
                "passport_num": "AB123456",
                "is_admin": True,
            },
        )
        stored = await fake_db.users.find_one({"username": "sneaky"})
        assert stored["is_admin"] is False

    async def test_rejects_invalid_email(self, client, fake_db):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "username": "test",
                "fullname": "Test User",
                "password": "password123",
                "passport_num": "AB123456",
            },
        )
        assert response.status_code == 422

    async def test_rejects_password_without_a_digit(self, client, fake_db):
        # The UI promised "8+ characters and a number"; the API enforced none.
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weak",
                "fullname": "Weak User",
                "password": "passwordonly",
                "passport_num": "AB123456",
            },
        )
        assert response.status_code == 422

    async def test_rejects_duplicate_username(self, client, fake_db, passenger):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "other@example.com",
                "username": "passenger",
                "fullname": "Impostor",
                "password": "password123",
                "passport_num": "AB123456",
            },
        )
        assert response.status_code == 409


class TestLogin:
    async def test_returns_a_bearer_token(self, client, passenger):
        response = await client.post("/api/auth/login", json=passenger)
        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"]

    async def test_rejects_a_wrong_password(self, client, passenger):
        response = await client.post(
            "/api/auth/login",
            json={"username": passenger["username"], "password": "wrongpassword1"},
        )
        assert response.status_code == 401

    async def test_rejects_an_unknown_user(self, client, fake_db):
        response = await client.post(
            "/api/auth/login",
            json={"username": "ghost", "password": "whatever123"},
        )
        assert response.status_code == 401

    async def test_error_does_not_reveal_whether_the_user_exists(
        self, client, passenger
    ):
        unknown = await client.post(
            "/api/auth/login", json={"username": "ghost", "password": "whatever123"}
        )
        wrong_password = await client.post(
            "/api/auth/login",
            json={"username": passenger["username"], "password": "wrongpassword1"},
        )
        assert unknown.json()["detail"] == wrong_password.json()["detail"]


class TestCurrentUser:
    async def test_me_returns_the_real_profile(self, client, passenger, auth_header):
        # The frontend previously invented this data from the JWT and showed
        # every user the literal name "User".
        headers = await auth_header(passenger)
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["fullname"] == "Test Passenger"
        assert response.json()["email"] == "passenger@example.com"
