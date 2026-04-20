import pytest
from fastapi.testclient import TestClient


class TestRegister:
    def test_register_success(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "full_name": "New User",
            "phone_number": "08098765432",
            "password": "SecurePass1!"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "hashed_password" not in data    # never expose this
        assert "password" not in data           # never expose this
        assert "id" in data
        assert data["role"] == "customer"
        assert data["is_verified"] is False

    def test_register_duplicate_email(self, client, registered_user):
        response = client.post("/api/v1/auth/register", json={
            "email": registered_user["email"],   # same email
            "full_name": "Duplicate User",
            "phone_number": "08011111111",
            "password": "SecurePass1!"
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["message"]

    def test_register_weak_password(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "weak@example.com",
            "full_name": "Weak Password",
            "phone_number": "08022222222",
            "password": "password"              # no uppercase, number, or special char
        })
        assert response.status_code == 422

    def test_register_invalid_phone(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "phone@example.com",
            "full_name": "Bad Phone",
            "phone_number": "12345",            # not a valid Nigerian number
            "password": "SecurePass1!"
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "full_name": "Bad Email",
            "phone_number": "08033333333",
            "password": "SecurePass1!"
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_user):
        response = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        response = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": "WrongPass1!"
        })
        assert response.status_code == 401
        # Must not reveal whether email exists
        assert "Invalid email or password" in response.json()["message"]

    def test_login_nonexistent_email(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "ghost@example.com",
            "password": "SecurePass1!"
        })
        assert response.status_code == 401
        # Same message as wrong password — timing attack prevention
        assert "Invalid email or password" in response.json()["message"]

    def test_login_missing_fields(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com"
            # missing password
        })
        assert response.status_code == 422


class TestProtectedRoutes:
    def test_access_protected_route_with_valid_token(
        self, client, auth_headers
    ):
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert "email" in response.json()

    def test_access_protected_route_without_token(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_access_protected_route_with_invalid_token(self, client):
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer completely.invalid.token"}
        )
        assert response.status_code == 401

    def test_admin_route_rejected_for_customer(
        self, client, auth_headers, registered_user
    ):
        # Get the user's ID first
        me = client.get("/api/v1/users/me", headers=auth_headers)
        user_id = me.json()["id"]

        # Try to access admin-only route with customer token
        response = client.get(
            f"/api/v1/users/{user_id}",
            headers=auth_headers
        )
        assert response.status_code == 401