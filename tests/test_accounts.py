import pytest


class TestCreateAccount:
    def test_create_savings_account(self, client, auth_headers):
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "NGN"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["account_type"] == "savings"
        assert data["currency"] == "NGN"
        assert data["status"] == "active"
        assert data["balance"] == "0.0000"
        assert len(data["account_number"]) == 10
        assert data["account_number"].startswith("000")

    def test_create_current_account(self, client, auth_headers):
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "current", "currency": "NGN"},
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["account_type"] == "current"

    def test_cannot_create_duplicate_account_type(
        self, client, auth_headers
    ):
        # Create first savings account
        client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "NGN"},
            headers=auth_headers
        )
        # Try to create a second savings account
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "NGN"},
            headers=auth_headers
        )
        assert response.status_code == 409

    def test_create_account_invalid_currency(
        self, client, auth_headers
    ):
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "XYZ"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_account_unauthenticated(self, client):
        response = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "NGN"}
        )
        assert response.status_code == 401


class TestGetAccount:
    def test_get_own_account(self, client, auth_headers):
        # Create account first
        created = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "NGN"},
            headers=auth_headers
        ).json()

        response = client.get(
            f"/api/v1/accounts/{created['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_cannot_get_another_users_account(self, client):
        """
        IDOR prevention test — user B cannot access user A's account.
        This is one of the most important security tests in the suite.
        """
        # Register and login user A
        client.post("/api/v1/auth/register", json={
            "email": "usera@example.com",
            "full_name": "User A",
            "phone_number": "08041111111",
            "password": "SecurePass1!"
        })
        token_a = client.post("/api/v1/auth/login", json={
            "email": "usera@example.com",
            "password": "SecurePass1!"
        }).json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User A creates an account
        account_a = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "NGN"},
            headers=headers_a
        ).json()

        # Register and login user B
        client.post("/api/v1/auth/register", json={
            "email": "userb@example.com",
            "full_name": "User B",
            "phone_number": "08042222222",
            "password": "SecurePass1!"
        })
        token_b = client.post("/api/v1/auth/login", json={
            "email": "userb@example.com",
            "password": "SecurePass1!"
        }).json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B tries to access User A's account
        response = client.get(
            f"/api/v1/accounts/{account_a['id']}",
            headers=headers_b
        )
        # Must be 404, not 403 — 403 would confirm the account exists
        assert response.status_code == 404

    def test_get_account_balance(self, client, auth_headers):
        created = client.post(
            "/api/v1/accounts",
            json={"account_type": "savings", "currency": "NGN"},
            headers=auth_headers
        ).json()

        response = client.get(
            f"/api/v1/accounts/{created['id']}/balance",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "as_of" in data
        assert data["currency"] == "NGN"

    def test_list_accounts(self, client, auth_headers):
        # Create two accounts
        client.post("/api/v1/accounts",
            json={"account_type": "savings", "currency": "NGN"},
            headers=auth_headers)
        client.post("/api/v1/accounts",
            json={"account_type": "current", "currency": "NGN"},
            headers=auth_headers)

        response = client.get("/api/v1/accounts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["accounts"]) == 2