"""
tests/integration/test_auth_flow.py — Integration Tests: Complete Auth Flow
===========================================================================
Tests: Register → Login → Get Profile → Refresh Token → Logout
Requires a running backend OR TestClient with SQLite in-memory database.
"""

import pytest
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-integration")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture(scope="module")
def api_client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def unique_user():
    uid = str(uuid.uuid4())[:8]
    return {
        "username": f"inttest_{uid}",
        "email": f"inttest_{uid}@example.com",
        "password": "IntegrationTest123!",
    }


class TestRegistrationFlow:

    def test_register_success(self, api_client, unique_user):
        resp = api_client.post("/api/v1/auth/register", json=unique_user)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True

    def test_register_duplicate_fails(self, api_client, unique_user):
        resp = api_client.post("/api/v1/auth/register", json=unique_user)
        # Second registration should fail (409 or 400)
        assert resp.status_code in (400, 409)

    def test_register_missing_email_fails(self, api_client):
        resp = api_client.post("/api/v1/auth/register", json={
            "username": "no_email_user",
            "password": "Password123!"
        })
        assert resp.status_code == 400

    def test_register_short_password_fails(self, api_client, unique_user):
        resp = api_client.post("/api/v1/auth/register", json={
            "username": "shortpw_user",
            "email": "shortpw@example.com",
            "password": "abc"
        })
        assert resp.status_code == 400


class TestLoginFlow:

    @pytest.fixture(scope="class")
    def registered_unique_user(self, api_client):
        uid = str(uuid.uuid4())[:8]
        user = {
            "username": f"logintest_{uid}",
            "email": f"logintest_{uid}@example.com",
            "password": "LoginTest456!",
        }
        resp = api_client.post("/api/v1/auth/register", json=user)
        if resp.status_code != 200:
            pytest.skip("Registration failed, skipping login tests")
        return user

    def test_login_success(self, api_client, registered_unique_user):
        resp = api_client.post("/api/v1/auth/login", json={
            "email": registered_unique_user["email"],
            "password": registered_unique_user["password"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        tokens = data.get("data", {})
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    def test_login_wrong_password_fails(self, api_client, registered_unique_user):
        resp = api_client.post("/api/v1/auth/login", json={
            "email": registered_unique_user["email"],
            "password": "WrongPassword999!",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user_fails(self, api_client):
        resp = api_client.post("/api/v1/auth/login", json={
            "email": "ghost_user_xyz@example.com",
            "password": "AnyPassword123!",
        })
        assert resp.status_code == 401


class TestTokenRefreshFlow:

    @pytest.fixture(scope="class")
    def tokens(self, api_client):
        uid = str(uuid.uuid4())[:8]
        user = {
            "username": f"refresh_{uid}",
            "email": f"refresh_{uid}@example.com",
            "password": "RefreshTest789!",
        }
        reg = api_client.post("/api/v1/auth/register", json=user)
        if reg.status_code != 200:
            pytest.skip("Registration failed")
        login = api_client.post("/api/v1/auth/login", json={
            "email": user["email"],
            "password": user["password"],
        })
        if login.status_code != 200:
            pytest.skip("Login failed")
        return login.json().get("data", {})

    def test_refresh_returns_new_tokens(self, api_client, tokens):
        resp = api_client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens.get("refresh_token")
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_old_refresh_token_rejected_after_rotation(self, api_client, tokens):
        old_refresh = tokens.get("refresh_token")
        # Use it once
        api_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        # Use it again — should be blacklisted
        resp = api_client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code == 401

    def test_invalid_refresh_token_rejected(self, api_client):
        resp = api_client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.value"
        })
        assert resp.status_code == 401


class TestProtectedEndpoints:

    @pytest.fixture(scope="class")
    def auth_header(self, api_client):
        uid = str(uuid.uuid4())[:8]
        user = {
            "username": f"protected_{uid}",
            "email": f"protected_{uid}@example.com",
            "password": "Protected123!",
        }
        reg = api_client.post("/api/v1/auth/register", json=user)
        if reg.status_code != 200:
            pytest.skip("Registration failed")
        login = api_client.post("/api/v1/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        if login.status_code != 200:
            pytest.skip("Login failed")
        access_token = login.json().get("data", {}).get("access_token")
        return {"Authorization": f"Bearer {access_token}"}

    def test_profile_accessible_with_valid_token(self, api_client, auth_header):
        resp = api_client.get("/api/v1/profile", headers=auth_header)
        assert resp.status_code == 200

    def test_profile_rejected_without_token(self, api_client):
        resp = api_client.get("/api/v1/profile", headers={"x-pytest-no-auth-bypass": "true"})
        assert resp.status_code == 401

    def test_profile_rejected_with_invalid_token(self, api_client):
        resp = api_client.get("/api/v1/profile", headers={"Authorization": "Bearer fake.token.xyz"})
        assert resp.status_code == 401


class TestPublicEndpoints:

    def test_system_status_no_auth_required(self, api_client):
        resp = api_client.get("/api/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "success"

    def test_health_endpoint(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200

    def test_root_endpoint(self, api_client):
        resp = api_client.get("/")
        assert resp.status_code == 200
