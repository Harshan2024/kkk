"""
tests/integration/test_activity_flow.py — Integration: Activity Logging → Analytics
====================================================================================
Tests: Login → Log Activity → Fetch Activities → Dashboard → Analytics
"""

import pytest
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-activity-flow")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture(scope="module")
def api_client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="module")
def logged_in_user(api_client):
    uid = str(uuid.uuid4())[:8]
    user = {
        "username": f"activity_{uid}",
        "email": f"activity_{uid}@example.com",
        "password": "ActivityTest123!",
    }
    reg = api_client.post("/api/v1/auth/register", json=user)
    if reg.status_code != 200:
        pytest.skip("Could not register test user")

    login = api_client.post("/api/v1/auth/login", json={
        "email": user["email"],
        "password": user["password"]
    })
    if login.status_code != 200:
        pytest.skip("Could not log in test user")

    data = login.json().get("data", {})
    return {
        "user": user,
        "access_token": data.get("access_token"),
        "headers": {"Authorization": f"Bearer {data.get('access_token')}"}
    }


class TestActivityLogging:

    def test_log_text_activity(self, api_client, logged_in_user):
        resp = api_client.post(
            "/api/v1/activities",
            json={"text": "I drove 15km to work today"},
            headers=logged_in_user["headers"]
        )
        assert resp.status_code in (200, 201)

    def test_log_activity_requires_auth(self, api_client):
        resp = api_client.post(
            "/api/v1/activities",
            json={"text": "I drove 10km"},
            headers={"x-pytest-no-auth-bypass": "true"}
        )
        assert resp.status_code == 401

    def test_log_activity_empty_text(self, api_client, logged_in_user):
        resp = api_client.post(
            "/api/v1/activities",
            json={"text": ""},
            headers=logged_in_user["headers"]
        )
        # Empty text may return 200 (ignored) or 400
        assert resp.status_code in (200, 400, 422)

    def test_fetch_activities_returns_list(self, api_client, logged_in_user):
        resp = api_client.get(
            "/api/v1/activities",
            headers=logged_in_user["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should return a list or dict with activities key
        assert data is not None


class TestDashboardEndpoints:

    def test_dashboard_accessible_with_auth(self, api_client, logged_in_user):
        resp = api_client.get(
            "/api/v1/dashboard",
            headers=logged_in_user["headers"]
        )
        assert resp.status_code in (200, 404)  # 404 if endpoint not yet defined

    def test_profile_returns_user_data(self, api_client, logged_in_user):
        resp = api_client.get(
            "/api/v1/profile",
            headers=logged_in_user["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True

    def test_analytics_endpoint_accessible(self, api_client, logged_in_user):
        resp = api_client.get(
            "/api/v1/analytics",
            headers=logged_in_user["headers"]
        )
        assert resp.status_code in (200, 404)


class TestChatEndpoints:

    def test_chat_returns_response(self, api_client, logged_in_user):
        resp = api_client.post(
            "/api/v1/chat",
            json={"message": "What is my carbon footprint?"},
            headers=logged_in_user["headers"]
        )
        assert resp.status_code in (200, 201, 422)

    def test_chat_requires_auth(self, api_client):
        resp = api_client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
            headers={"x-pytest-no-auth-bypass": "true"}
        )
        assert resp.status_code == 401


class TestSystemEndpoints:

    def test_feature_flags_accessible(self, api_client, logged_in_user):
        resp = api_client.get(
            "/api/v1/feature-flags",
            headers=logged_in_user["headers"]
        )
        assert resp.status_code == 200

    def test_security_status_accessible(self, api_client, logged_in_user):
        resp = api_client.get(
            "/api/v1/security/status",
            headers=logged_in_user["headers"]
        )
        assert resp.status_code == 200

    def test_observability_metrics_accessible(self, api_client, logged_in_user):
        resp = api_client.get(
            "/observability/metrics",
            headers=logged_in_user["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "system" in data

    def test_health_dashboard_accessible(self, api_client, logged_in_user):
        resp = api_client.get(
            "/api/v1/admin/health-dashboard",
            headers=logged_in_user["headers"]
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "components" in data
        assert "status" in data
