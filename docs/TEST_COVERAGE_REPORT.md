# CarbonTracker AI — Test Coverage Report

**Version:** 1.1.0 | **Date:** 2026-07-05 | **Phase:** 12

---

## Overview

The test suite is organized into three layers following the testing pyramid:

```
              ┌──────────────┐
              │ Load Tests   │  ← Locust (production-like traffic)
              │  (1 file)    │
            ┌─┴──────────────┴─┐
            │ Integration Tests │  ← FastAPI TestClient (HTTP level)
            │   (2 files)      │
          ┌─┴──────────────────┴─┐
          │     Unit Tests        │  ← Pure Python, no I/O
          │    (3 files)          │
          └───────────────────────┘
```

---

## Test Suite Summary

| File | Type | Tests | Coverage Target |
|---|---|---|---|
| `tests/unit/test_sanitizer.py` | Unit | 22 | ≥ 95% sanitizer.py |
| `tests/unit/test_auth.py` | Unit | 27 | ≥ 90% jwt_service + password_service + metrics |
| `tests/unit/test_carbon_calc.py` | Unit | 11 | ≥ 80% calculation engine |
| `tests/integration/test_auth_flow.py` | Integration | 19 | Auth flow end-to-end |
| `tests/integration/test_activity_flow.py` | Integration | 14 | Activity + dashboard flow |
| `tests/load/locustfile.py` | Load | N/A | Throughput + error rate |
| **Total** | | **93 tests** | |

---

## Unit Tests

### `test_sanitizer.py` — Input Sanitization

**Coverage:** `app/utils/sanitizer.py`

| Class | Tests | Description |
|---|---|---|
| `TestSanitizeText` | 13 | XSS script tags, img onerror, iframe, javascript: protocol, unicode, whitespace |
| `TestSanitizeFilename` | 12 | Path traversal (unix/windows), null bytes, special chars, empty, leading dot |
| `TestSanitizeSearchQuery` | 3 | Query XSS, empty input |

**Key validations:**
- `<script>` tags are HTML-escaped → `&lt;script&gt;`
- `../../../etc/passwd` → `passwd` (no path traversal possible)
- `\x00` null bytes stripped
- Unicode characters (CO₂e, 🌿) preserved

---

### `test_auth.py` — Authentication & Metrics

**Coverage:** `app/auth/jwt_service.py`, `app/auth/password_service.py`, `app/utils/metrics.py`

#### Password Service (9 tests)
- Hash returns string, not plaintext
- Correct password verifies → True
- Wrong password verifies → False
- Empty/None hash → False (safe)
- Same password → different hashes (bcrypt salt)
- Unicode passwords supported

#### JWT Service (10 tests)
- Access token is string, contains `sub` claim
- Refresh token has `refresh: True` flag
- Invalid/tampered token → None
- Blacklisted token is_blacklisted → True
- Token contains `exp` field

#### Metrics Thread Safety (8 tests)
- Counters increment correctly
- `record_request()` tracks success/error counts
- Cache hit ratio calculation
- p50 latency percentile
- **100-thread concurrent increment** → exact count (no races)

---

### `test_carbon_calc.py` — Carbon Engine

**Coverage:** `app/calculations/engines.py`, `app/nlp/parser.py`

| Class | Tests | Description |
|---|---|---|
| `TestCarbonCalculations` | 5 | Zero hours, valid appliance, unknown appliance, proportional scaling |
| `TestNLPParser` | 4 | Food/transport parsing, empty string, long text no crash |
| `TestEmissionFactorSeeding` | 2 | Module import checks |
| `TestSustainabilityScore` | 2 | Service import checks |

All tests gracefully skip if modules are unavailable in the test environment.

---

## Integration Tests

### `test_auth_flow.py` — Complete Auth Flow

**Tests:** Register → Login → Token Refresh → Protected Endpoints → Public Endpoints

| Class | Tests | Description |
|---|---|---|
| `TestRegistrationFlow` | 4 | Success, duplicate, missing email, short password |
| `TestLoginFlow` | 3 | Success, wrong password, nonexistent user |
| `TestTokenRefreshFlow` | 3 | New tokens returned, old refresh rejected, invalid rejected |
| `TestProtectedEndpoints` | 3 | Valid token, no token (401), invalid token (401) |
| `TestPublicEndpoints` | 3 | System status, health, root |

**Key validations:**
- Duplicate registration → HTTP 400/409
- Wrong password → HTTP 401 (not 500)
- Expired/tampered token → HTTP 401
- Protected endpoints without auth → HTTP 401
- Token rotation: reusing old refresh token → HTTP 401

---

### `test_activity_flow.py` — Activity + Dashboard Flow

| Class | Tests | Description |
|---|---|---|
| `TestActivityLogging` | 4 | Text log, auth required, empty text, fetch list |
| `TestDashboardEndpoints` | 3 | Dashboard, profile, analytics |
| `TestChatEndpoints` | 2 | Chat response, auth required |
| `TestSystemEndpoints` | 4 | Feature flags, security status, observability, health-dashboard |

---

## Load Testing (`locustfile.py`)

### Configuration

| Parameter | Value |
|---|---|
| Target Users | 100 |
| Spawn Rate | 10/s |
| Test Duration | 60 seconds |
| Anonymous Users | 20% (health checks, status) |
| Authenticated Users | 80% (full application flow) |

### Task Weight Distribution (Authenticated)

| Task | Weight | Expected RPS at 80 users |
|---|---|---|
| Log Activity | 8 | ~12 rps |
| Fetch Activities | 6 | ~9 rps |
| Fetch Profile | 5 | ~7.5 rps |
| Chat Query | 4 | ~6 rps |
| Fetch Analytics | 3 | ~4.5 rps |
| Recommendations | 2 | ~3 rps |
| System Status | 2 | ~3 rps |
| Token Refresh | 1 | ~1.5 rps |
| Achievements | 1 | ~1.5 rps |

### Pass/Fail Criteria

| Metric | Threshold |
|---|---|
| Error rate | < 10% |
| p95 response time | < 2000ms |
| p99 response time | < 5000ms |

---

## Running Tests

### Unit Tests
```bash
cd backend
pip install pytest pytest-asyncio httpx

# Run all unit tests
pytest tests/unit/ -v --tb=short

# Run with coverage
pip install pytest-cov
pytest tests/unit/ --cov=app --cov-report=html
```

### Integration Tests
```bash
# Requires: DATABASE_URL pointing to a test DB (or SQLite in-memory)
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="test-secret-key"
pytest tests/integration/ -v --tb=short
```

### Load Tests
```bash
pip install locust
locust -f tests/load/locustfile.py --host=http://127.0.0.1:8001 --headless \
  -u 100 -r 10 --run-time 60s
```

---

## Known Limitations

1. Carbon calc tests skip gracefully if the calculation engine is not importable in CI
2. Integration tests use SQLite (in-memory) which may not replicate all PostgreSQL behavior
3. Load tests assume a running backend — not executed in the GitHub Actions CI pipeline (by design)
4. NLP tests are skipped if spaCy model is not downloaded
