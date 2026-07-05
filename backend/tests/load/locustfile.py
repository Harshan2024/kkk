"""
tests/load/locustfile.py — Load Testing for CarbonTracker AI
=============================================================
Phase 12: Load Testing with Locust

Usage:
    locust -f tests/load/locustfile.py --host=http://127.0.0.1:8001

Web UI: http://localhost:8089
Configure: 100 users, spawn rate 10/s, run for 60s

Simulates:
- Anonymous health checks
- User login
- Activity logging
- Dashboard fetches
- AI chat queries
- Analytics requests
"""

import random
import json
from locust import HttpUser, task, between, events
from locust.exception import StopUser


# ─── Shared test credentials pool ────────────────────────────────────────────
TEST_EMAIL = "loadtest@carbontracker.test"
TEST_PASSWORD = "LoadTest123!"
TEST_USERNAME = "load_test_user"

ACTIVITY_SAMPLES = [
    "I drove 10km to work today",
    "Ate a beef burger for lunch",
    "Used air conditioning for 3 hours",
    "Took a 20-minute shower",
    "Bought new clothes online",
    "Flew 500km for a business trip",
    "Cooked dinner on gas stove",
    "Watched TV for 2 hours",
    "Cycled to the grocery store",
    "Worked from home all day",
]

CHAT_MESSAGES = [
    "What is my carbon footprint?",
    "How can I reduce my emissions?",
    "Compare my food vs transport impact",
    "What are my top 3 emission sources?",
    "Give me sustainability tips",
]


# ─── Anonymous User (unauthenticated load) ────────────────────────────────────
class AnonymousUser(HttpUser):
    """
    Simulates unauthenticated traffic — health checks and status endpoints.
    Weight: 20% of virtual users.
    """
    weight = 2
    wait_time = between(1, 3)

    @task(3)
    def check_system_status(self):
        self.client.get("/api/system/status", name="/api/system/status")

    @task(1)
    def check_health(self):
        self.client.get("/health", name="/health")

    @task(1)
    def check_root(self):
        self.client.get("/", name="/")


# ─── Authenticated User (main application load) ───────────────────────────────
class AuthenticatedUser(HttpUser):
    """
    Simulates logged-in users performing typical CarbonTracker workflows.
    Weight: 80% of virtual users.
    """
    weight = 8
    wait_time = between(1, 4)

    def on_start(self):
        """Login and acquire auth token at user start."""
        self.access_token = None
        self.refresh_token = None
        self._login()

    def _login(self):
        """Attempt login; stop user if login fails."""
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            name="/api/v1/auth/login [setup]"
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
        elif resp.status_code == 401:
            # Try registering first
            self.client.post("/api/v1/auth/register", json={
                "username": TEST_USERNAME,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }, name="/api/v1/auth/register [setup]")
            self._login()

    def _headers(self):
        if not self.access_token:
            raise StopUser()
        return {"Authorization": f"Bearer {self.access_token}"}

    @task(5)
    def fetch_profile(self):
        self.client.get("/api/v1/profile", headers=self._headers(), name="/api/v1/profile")

    @task(8)
    def log_activity(self):
        text = random.choice(ACTIVITY_SAMPLES)
        self.client.post(
            "/api/v1/activities",
            json={"text": text},
            headers=self._headers(),
            name="/api/v1/activities [POST]"
        )

    @task(6)
    def fetch_activities(self):
        self.client.get(
            "/api/v1/activities?limit=20&offset=0",
            headers=self._headers(),
            name="/api/v1/activities [GET]"
        )

    @task(4)
    def chat_query(self):
        msg = random.choice(CHAT_MESSAGES)
        self.client.post(
            "/api/v1/chat",
            json={"message": msg},
            headers=self._headers(),
            name="/api/v1/chat"
        )

    @task(3)
    def fetch_analytics(self):
        self.client.get(
            "/api/v1/analytics",
            headers=self._headers(),
            name="/api/v1/analytics"
        )

    @task(2)
    def fetch_recommendations(self):
        self.client.get(
            "/api/v1/recommendations",
            headers=self._headers(),
            name="/api/v1/recommendations"
        )

    @task(2)
    def check_system_status(self):
        self.client.get("/api/system/status", name="/api/system/status")

    @task(1)
    def fetch_achievements(self):
        self.client.get(
            "/api/v1/achievements",
            headers=self._headers(),
            name="/api/v1/achievements"
        )

    @task(1)
    def refresh_token_task(self):
        if not self.refresh_token:
            return
        resp = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": self.refresh_token},
            name="/api/v1/auth/refresh"
        )
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data.get("access_token", self.access_token)
            self.refresh_token = data.get("refresh_token", self.refresh_token)


# ─── Event hooks for reporting ────────────────────────────────────────────────
@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Print final summary on test completion."""
    if environment.stats.total.fail_ratio > 0.1:
        print(f"\n[LOAD TEST] FAIL: Error rate {environment.stats.total.fail_ratio:.1%} exceeds 10% threshold")
        environment.process_exit_code = 1
    else:
        print(f"\n[LOAD TEST] PASS: Error rate {environment.stats.total.fail_ratio:.1%} within acceptable threshold")
