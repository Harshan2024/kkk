# CarbonTracker AI — Load Test Report

**Version:** 1.1.0 | **Date:** 2026-07-05 | **Phase:** 12

---

## Test Configuration

| Parameter | Value |
|---|---|
| Tool | Locust 2.24+ |
| Target Host | `http://127.0.0.1:8001` |
| Virtual Users | 100 |
| Spawn Rate | 10 users/second |
| Test Duration | 60 seconds |
| Ramp-up Time | 10 seconds |
| Total Requests (estimated) | ~2,800–3,500 |

---

## User Profiles

### Anonymous User (20 VUs)
- Health check: `GET /api/system/status`
- Heartbeat: `GET /health`
- Root: `GET /`

### Authenticated User (80 VUs)
- Full user journey: login → log activities → view dashboard → chat → analytics

---

## Expected Performance Targets

| Metric | Green (Pass) | Yellow (Warning) | Red (Fail) |
|---|---|---|---|
| Error Rate | < 1% | 1–10% | > 10% |
| p50 Response Time | < 200ms | 200–500ms | > 500ms |
| p95 Response Time | < 1000ms | 1000–2000ms | > 2000ms |
| p99 Response Time | < 2000ms | 2000–5000ms | > 5000ms |
| Throughput | > 40 rps | 20–40 rps | < 20 rps |

---

## Simulated Test Results (Baseline)

> **Note:** These are projected results based on the system architecture. Run `locust -f tests/load/locustfile.py --host=http://127.0.0.1:8001` to obtain real measurements.

| Endpoint | Method | Median (ms) | p95 (ms) | Error % |
|---|---|---|---|---|
| `/api/system/status` | GET | 8 | 15 | 0.0% |
| `/health` | GET | 5 | 10 | 0.0% |
| `/api/v1/auth/login` | POST | 45 | 120 | 0.0% |
| `/api/v1/auth/refresh` | POST | 35 | 90 | 0.0% |
| `/api/v1/profile` | GET | 25 | 60 | 0.0% |
| `/api/v1/activities` | POST | 280 | 650 | < 1% |
| `/api/v1/activities` | GET | 40 | 100 | 0.0% |
| `/api/v1/chat` | POST | 450 | 1200 | < 2% |
| `/api/v1/analytics` | GET | 35 | 80 | 0.0% |
| `/api/v1/recommendations` | GET | 55 | 140 | 0.0% |
| `/api/v1/achievements` | GET | 30 | 75 | 0.0% |

**Overall Error Rate:** ~0.3% (primarily from NLP timeout on complex activity text)

---

## Bottleneck Analysis

### Primary Bottleneck: NLP + Carbon Calculation
`POST /api/v1/activities` is the slowest endpoint due to:
1. spaCy NLP pipeline execution (~100–200ms)
2. Carbon emission calculation
3. Database write + achievement check

**Mitigation in place:**
- In-memory cache for repeated inputs
- Circuit breaker to prevent NLP cascade failures

### Secondary Bottleneck: AI Chat
`POST /api/v1/chat` is slow when using OpenAI API:
- Without API key: < 100ms (NLP fallback)
- With OpenAI: 400–1200ms (external API latency)

**Mitigation:** Circuit breaker limits to 50 concurrent AI requests. Falls back gracefully.

---

## Scalability Projections

| Concurrent Users | Expected RPS | Required Instances | Recommended |
|---|---|---|---|
| 50 | ~25 | 1 | Current setup |
| 100 | ~48 | 1 (2 workers) | Current setup |
| 500 | ~220 | 3 | Add Redis + load balancer |
| 2,000 | ~800 | 8 | Kubernetes + Redis + read replicas |
| 10,000+ | ~4,000 | 20+ | Full microservices + Kafka |

---

## Running the Load Test

### Prerequisites
```bash
pip install locust

# Ensure backend is running
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8001

# Create test user (first time only)
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"load_test_user","email":"loadtest@carbontracker.test","password":"LoadTest123!"}'
```

### Web UI Mode (Interactive)
```bash
locust -f tests/load/locustfile.py --host=http://127.0.0.1:8001
# Open: http://localhost:8089
```

### Headless Mode (CI/Automated)
```bash
locust -f tests/load/locustfile.py \
  --host=http://127.0.0.1:8001 \
  --headless \
  -u 100 -r 10 \
  --run-time 60s \
  --html=load_test_report.html
```

### CSV Output
```bash
locust -f tests/load/locustfile.py \
  --host=http://127.0.0.1:8001 \
  --headless -u 100 -r 10 --run-time 60s \
  --csv=results/load_test_$(date +%Y%m%d)
```

---

## Pass/Fail Criteria

The load test automatically exits with error code 1 if:
- Error rate exceeds 10%

This is configured in the `on_quitting` event hook in `locustfile.py`.

For CI integration, run:
```bash
locust -f tests/load/locustfile.py --host=$BACKEND_URL --headless \
  -u 50 -r 5 --run-time 30s
echo "Exit code: $?"
# Non-zero = load test failed
```
