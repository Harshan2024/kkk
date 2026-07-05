"""
tests/unit/test_auth.py — Unit Tests for Authentication Services
================================================================
Coverage target: ≥ 90% of auth/password_service.py and auth/jwt_service.py
Tests JWT creation, expiry, blacklisting, and password hashing.
"""

import pytest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ─── Password Service Tests ──────────────────────────────────────────────────

class TestPasswordService:

    def setup_method(self):
        from app.auth.password_service import PasswordService
        self.svc = PasswordService

    def test_hash_password_returns_string(self):
        hashed = self.svc.hash_password("MySecurePassword123!")
        assert isinstance(hashed, str)
        assert len(hashed) > 20

    def test_hash_is_not_plaintext(self):
        hashed = self.svc.hash_password("plaintext")
        assert hashed != "plaintext"

    def test_verify_correct_password(self):
        pw = "CorrectPassword456!"
        hashed = self.svc.hash_password(pw)
        assert self.svc.verify_password(pw, hashed) is True

    def test_verify_wrong_password(self):
        hashed = self.svc.hash_password("correct_pw")
        assert self.svc.verify_password("wrong_pw", hashed) is False

    def test_verify_empty_hash_returns_false(self):
        assert self.svc.verify_password("anything", "") is False

    def test_verify_none_hash_returns_false(self):
        assert self.svc.verify_password("anything", None) is False

    def test_different_passwords_produce_different_hashes(self):
        h1 = self.svc.hash_password("password1")
        h2 = self.svc.hash_password("password2")
        assert h1 != h2

    def test_same_password_produces_different_hashes_due_to_salt(self):
        """bcrypt uses random salt — same password → different hash each time."""
        h1 = self.svc.hash_password("same_pw")
        h2 = self.svc.hash_password("same_pw")
        assert h1 != h2
        # But both should verify correctly
        assert self.svc.verify_password("same_pw", h1)
        assert self.svc.verify_password("same_pw", h2)

    def test_unicode_password(self):
        pw = "PasswordWith🔒Unicode"
        hashed = self.svc.hash_password(pw)
        assert self.svc.verify_password(pw, hashed) is True


# ─── JWT Service Tests ────────────────────────────────────────────────────────

class TestJWTService:

    def setup_method(self):
        os.environ.setdefault("SECRET_KEY", "test-jwt-secret-key-for-unit-tests")
        from app.auth.jwt_service import JWTService
        self.svc = JWTService

    def test_create_access_token_returns_string(self):
        token = self.svc.create_access_token({"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_refresh_token_returns_string(self):
        token = self.svc.create_refresh_token({"sub": "testuser"})
        assert isinstance(token, str)

    def test_decode_access_token_returns_payload(self):
        token = self.svc.create_access_token({"sub": "testuser123"})
        payload = self.svc.decode_token(token)
        assert payload is not None
        assert payload.get("sub") == "testuser123"

    def test_decode_refresh_token_has_refresh_flag(self):
        token = self.svc.create_refresh_token({"sub": "testuser"})
        payload = self.svc.decode_token(token)
        assert payload is not None
        assert payload.get("refresh") is True

    def test_decode_invalid_token_returns_none(self):
        payload = self.svc.decode_token("not.a.valid.token")
        assert payload is None

    def test_decode_tampered_token_returns_none(self):
        token = self.svc.create_access_token({"sub": "user"})
        tampered = token[:-5] + "XXXXX"
        payload = self.svc.decode_token(tampered)
        assert payload is None

    def test_blacklist_token(self):
        token = self.svc.create_access_token({"sub": "blacklistuser"})
        assert not self.svc.is_blacklisted(token)
        self.svc.blacklist_token(token)
        assert self.svc.is_blacklisted(token)

    def test_different_tokens_for_different_users(self):
        t1 = self.svc.create_access_token({"sub": "user1"})
        t2 = self.svc.create_access_token({"sub": "user2"})
        assert t1 != t2

    def test_token_contains_expiry(self):
        token = self.svc.create_access_token({"sub": "exptest"})
        payload = self.svc.decode_token(token)
        assert "exp" in payload

    def test_access_and_refresh_tokens_differ(self):
        access = self.svc.create_access_token({"sub": "user"})
        refresh = self.svc.create_refresh_token({"sub": "user"})
        assert access != refresh


# ─── Metrics Unit Tests ───────────────────────────────────────────────────────

class TestObservabilityMetrics:

    def setup_method(self):
        from app.utils.metrics import ObservabilityMetrics
        self.metrics = ObservabilityMetrics()

    def test_increment_db_retries(self):
        self.metrics.increment("db_retries")
        assert self.metrics.db_retries == 1

    def test_increment_multiple_times(self):
        for _ in range(5):
            self.metrics.increment("ai_failures")
        assert self.metrics.ai_failures == 5

    def test_increment_unknown_field_ignored(self):
        self.metrics.increment("nonexistent_field")  # Should not raise
        assert not hasattr(self.metrics, "nonexistent_field")

    def test_record_request_success(self):
        self.metrics.record_request("/api/v1/activities", 200, 45.2)
        ep = self.metrics._endpoints["/api/v1/activities"]
        s = ep.summary()
        assert s["request_count"] == 1
        assert s["success_count"] == 1
        assert s["error_count"] == 0

    def test_record_request_error(self):
        self.metrics.record_request("/api/v1/chat", 500, 120.0)
        ep = self.metrics._endpoints["/api/v1/chat"]
        s = ep.summary()
        assert s["error_count"] == 1

    def test_cache_hit_ratio(self):
        self.metrics.record_cache_hit()
        self.metrics.record_cache_hit()
        self.metrics.record_cache_miss()
        ratio = self.metrics.cache_hit_ratio()
        assert ratio == pytest.approx(66.67, abs=0.1)

    def test_cache_hit_ratio_none_when_empty(self):
        m = type(self.metrics)()
        assert m.cache_hit_ratio() is None

    def test_uptime_positive(self):
        time.sleep(0.15)
        assert self.metrics.uptime_seconds() > 0

    def test_get_summary_structure(self):
        summary = self.metrics.get_summary()
        assert "collected_at" in summary
        assert "system" in summary
        assert "endpoints" in summary

    def test_latency_percentile(self):
        for ms in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            self.metrics.record_request("/test", 200, float(ms))
        ep = self.metrics._endpoints["/test"]
        p50 = ep.latency.percentile(50)
        assert p50 is not None
        assert 40 <= p50 <= 60

    def test_thread_safety_concurrent_increments(self):
        import threading
        m = type(self.metrics)()
        threads = [threading.Thread(target=lambda: m.increment("rate_limit_hits")) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert m.rate_limit_hits == 100
