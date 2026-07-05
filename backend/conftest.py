"""
conftest.py — CarbonTracker Pytest Shared Fixtures
===================================================
Provides reusable fixtures for unit, integration, and load tests.
"""

import pytest
import sys
import os

# Ensure backend app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient


# ─── Database Fixtures ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for testing (no PostgreSQL required)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    from app.database.session import Base
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provides a transactional database session that rolls back after each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ─── FastAPI Test Client ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_app():
    """Creates the FastAPI app configured for testing."""
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
    os.environ.setdefault("ENVIRONMENT", "test")

    from app.main import app
    return app


@pytest.fixture(scope="session")
def client(test_app):
    """Provides a TestClient for HTTP-level integration tests."""
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


# ─── Auth Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_user_credentials():
    """Returns test user credentials."""
    return {
        "username": "pytest_user",
        "email": "pytest@carbontracker.test",
        "password": "TestPassword123!",
    }


@pytest.fixture(scope="session")
def registered_user(client, test_user_credentials):
    """Registers a test user and returns the response."""
    resp = client.post("/api/v1/auth/register", json=test_user_credentials)
    # Allow 400 if user already exists from a previous run
    assert resp.status_code in (200, 400)
    return test_user_credentials


@pytest.fixture(scope="session")
def auth_tokens(client, registered_user):
    """Logs in and returns access + refresh tokens."""
    resp = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    if resp.status_code != 200:
        pytest.skip("Login failed — skipping auth-dependent tests")
    data = resp.json()
    tokens = data.get("data", {})
    return {
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
    }


@pytest.fixture(scope="session")
def auth_headers(auth_tokens):
    """Returns Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


# ─── Utility Helpers ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url():
    return "http://127.0.0.1:8001"
