# CarbonTracker AI — Monitoring Report

**Version:** 1.1.0 | **Date:** 2026-07-05 | **Phase:** 11

---

## Overview

CarbonTracker AI implements a production-grade observability stack with metrics collection, structured logging, health dashboards, and alert dispatching.

---

## Metrics System (`app/utils/metrics.py`)

### Global Counters

| Metric | Description |
|---|---|
| `db_retries` | Database query retry attempts |
| `circuit_breaker_opens` | Circuit breaker trip events |
| `cache_hits` | In-memory cache hits |
| `cache_misses` | In-memory cache misses |
| `ai_failures` | AI service failure count |
| `rate_limit_hits` | Rate-limited request count |
| `auth_successes` | Successful authentication events |
| `auth_failures` | Failed authentication attempts |
| `active_users` | Currently active user sessions (gauge) |
| `background_jobs_run` | Background task executions |

### Per-Endpoint Tracking

Each API endpoint tracks:
- `request_count` — total requests
- `success_count` — HTTP 2xx responses
- `error_count` — HTTP 4xx/5xx responses
- `latency_ms` — Histogram with p50/p95/p99 percentiles

### Cache Statistics

```json
{
  "cache_hits": 4521,
  "cache_misses": 812,
  "cache_hit_ratio_pct": 84.77
}
```

### Endpoints

| Endpoint | Auth | Response |
|---|---|---|
| `GET /observability/metrics` | None | Full metrics JSON |
| `GET /api/v1/admin/health-dashboard` | Bearer | Traffic-light status |
| `GET /api/system/status` | None | Simple status |
| `GET /health` | None | Heartbeat |

---

## Structured Logging (`app/utils/audit_logger.py`)

Every log entry includes:

```json
{
  "timestamp": "2026-07-05T10:23:45.123456Z",
  "level": "INFO",
  "service": "auth",
  "message": "User login successful",
  "request_id": "req-abc123",
  "context": {
    "user_id": "usr-xyz",
    "endpoint": "/api/v1/auth/login",
    "duration_ms": 42.3,
    "status_code": 200
  }
}
```

### Logged Events

| Event | Level | Service |
|---|---|---|
| Successful login | INFO | auth |
| Failed login | WARNING | auth |
| Token refresh | INFO | auth |
| Logout | INFO | auth |
| Activity logged | INFO | activity |
| AI chat message | INFO | ai_coach |
| Rate limit hit | WARNING | rate_limiter |
| Circuit breaker open | WARNING | circuit_breaker |
| DB retry | WARNING | database |
| 5xx error | ERROR | api |

### Credential Filtering

Passwords, tokens, and secret keys are **never logged**. The sanitizer filters:
- `password`, `hashed_password`
- `access_token`, `refresh_token`
- `secret_key`, `api_key`

---

## Alert Notification System (`app/utils/notifier.py`)

### Alert Levels

| Level | Trigger | Default Channels |
|---|---|---|
| `DEBUG` | Development only | Log file |
| `INFO` | Normal operations | Log file |
| `WARNING` | Degraded state | Log + Slack (if configured) |
| `ERROR` | Recoverable errors | Log + Slack + Email |
| `CRITICAL` | Service outage | All channels |

### Alert Channels

| Channel | Activated By |
|---|---|
| Log | Always active |
| Email | `ALERT_EMAIL_SMTP_HOST` env var |
| Slack | `ALERT_SLACK_WEBHOOK_URL` env var |
| Discord | `ALERT_DISCORD_WEBHOOK_URL` env var |
| Teams | `ALERT_TEAMS_WEBHOOK_URL` env var |

### Configuration

```env
ALERT_MIN_LEVEL=error           # Minimum level to dispatch
ALERT_SLACK_WEBHOOK_URL=...     # Slack incoming webhook
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_FROM=alerts@domain.com
ALERT_EMAIL_TO=oncall@domain.com
ALERT_EMAIL_PASSWORD=<app-password>
```

---

## Health Dashboard

`GET /api/v1/admin/health-dashboard` returns:

```json
{
  "status": "healthy",
  "timestamp": "2026-07-05T10:23:45Z",
  "uptime_seconds": 86412,
  "components": {
    "backend":          { "status": "online",    "indicator": "green" },
    "database":         { "status": "online",    "indicator": "green" },
    "cache":            { "status": "healthy",   "indicator": "green" },
    "ai_engine":        { "status": "online",    "indicator": "green" },
    "circuit_breakers": { "status": "ok",        "indicator": "green", "opens": 0 },
    "resources": {
      "indicator": "green",
      "cpu_pct": 12.4,
      "memory_pct": 38.2,
      "disk_pct": 22.1
    }
  }
}
```

### Traffic Light Logic

| Component | Green | Yellow | Red |
|---|---|---|---|
| Database | Connected | N/A | Unreachable |
| Cache | Healthy | Degraded | Failed |
| Resources | CPU<60%, Mem<70% | CPU<75%, Mem<85% | CPU>90%, Mem>85% |
| Circuit Breakers | Opens=0–3 | Opens=4–10 | Opens>10 |

---

## Frontend Admin Panel

The admin panel at `/admin` provides a real-time visual version of the health dashboard:
- Auto-refreshes every 30 seconds
- Color-coded component status indicators
- CPU/Memory/Disk metric cards
- Reliability counter display
- Uptime display

---

## Recommended Monitoring Stack (Future)

For production scale, consider adding:

| Tool | Purpose |
|---|---|
| **Prometheus** | Scrape `/observability/metrics` for time-series storage |
| **Grafana** | Dashboard visualization from Prometheus data |
| **Loki** | Log aggregation from structured JSON logs |
| **PagerDuty** | On-call alert routing from Slack/email alerts |
| **Sentry** | Error tracking and stack traces |
