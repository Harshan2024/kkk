# CarbonTracker AI — Changelog

All notable changes to CarbonTracker AI are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] — 2026-07-05 — Enterprise Readiness Release

### Added (Phase 11 — Observability)
- Production-grade `ObservabilityMetrics` with per-endpoint latency histograms (p50/p95/p99), cache hit/miss ratios, auth event counters, and background job tracking
- `notifier.py` — Pluggable alert abstraction layer with stubs for Email, Slack, Discord, and Microsoft Teams
- Re-enabled `/observability/metrics` endpoint with full metrics summary
- New `/api/v1/admin/health-dashboard` endpoint with traffic-light (green/yellow/red) component status
- Automatic request metrics recording in timing middleware

### Added (Phase 12 — Testing)
- `conftest.py` — Shared pytest fixtures (in-memory SQLite, TestClient, auth helpers)
- `tests/unit/test_sanitizer.py` — 20 unit tests for XSS and path traversal prevention
- `tests/unit/test_auth.py` — 25 unit tests for JWT, password hashing, and metrics thread-safety
- `tests/unit/test_carbon_calc.py` — Unit tests for carbon calculation engine and NLP parser
- `tests/integration/test_auth_flow.py` — Complete registration → login → refresh → logout integration tests
- `tests/integration/test_activity_flow.py` — Full activity logging → dashboard → analytics flow tests
- `tests/load/locustfile.py` — Locust load test simulating 100 concurrent users (80% authenticated, 20% anonymous)
- Added `pytest-asyncio`, `httpx`, `psutil` to requirements

### Added (Phase 13 — Deployment & DevOps)
- `backend/Dockerfile` — Multi-stage production Docker image (Python 3.12, non-root user, health check)
- `frontend/Dockerfile` — Multi-stage Next.js 14 standalone Docker image (Node.js 20, non-root user)
- `docker-compose.yml` — Full stack orchestration (PostgreSQL, backend, frontend, Nginx)
- `backend/.env.development`, `.env.staging`, `.env.production` — Environment configuration templates
- `nginx/nginx.conf` — Production Nginx with HTTPS, rate limiting, gzip, security headers
- `.github/workflows/ci.yml` — GitHub Actions CI with lint, unit tests, build, Docker validation, security audit

### Added (Phase 14 — Production Operations)
- `backend/scripts/backup.py` — Automated PostgreSQL backup with daily/weekly/monthly rotation
- `backend/scripts/restore.py` — Backup restore with integrity verification and history logging
- `backend/scripts/log_rotate.py` — Log compression (>7 days) and deletion (>30 days) with dry-run mode
- `CHANGELOG.md` — This file. Semantic versioning documentation

### Added (Phase 15 — Scalability)
- `backend/app/cache/redis_adapter.py` — Redis-ready cache adapter with in-memory fallback (activated by `REDIS_URL`)
- `backend/app/queue/task_queue.py` — Message queue abstraction with in-process and RabbitMQ/Kafka stubs
- `frontend/public/manifest.json` — PWA web app manifest (installable, standalone display mode)
- `frontend/public/sw.js` — Service Worker with offline-first cache strategy and background sync stub
- `backend/app/auth/rbac.py` — Role-based access control (`user`, `moderator`, `admin`, `super_admin`)
- `frontend/app/admin/page.tsx` — Admin dashboard with system health, user management architecture
- `next.config.mjs` — Updated with PWA service worker headers and standalone output mode

### Added (Documentation)
- `docs/SYSTEM_ARCHITECTURE_REPORT.md`
- `docs/MONITORING_REPORT.md`
- `docs/TEST_COVERAGE_REPORT.md`
- `docs/LOAD_TEST_REPORT.md`
- `docs/DEPLOYMENT_GUIDE.md`
- `docs/DOCKER_SETUP.md`
- `docs/CI_CD_PIPELINE.md`
- `docs/PRODUCTION_RUNBOOK.md`
- `docs/DISASTER_RECOVERY_GUIDE.md`
- `docs/VERSIONING_STRATEGY.md`
- `docs/FINAL_PRODUCTION_READINESS_REPORT.md`

### Fixed
- `endpoints.py` — `login_user_endpoint` audit log crash: `payload.username` → `payload.email` (AttributeError on failed login now returns HTTP 401 correctly)

### Security
- All security headers active (HSTS, CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy, COEP, CORP, COOP)
- Input sanitization on all user-facing text and file upload endpoints
- Structured audit logging for all authentication events
- Credential filtering in audit logs (password/token fields never logged)

---

## [1.0.0] — 2026-07-02 — Initial Production Release

### Added (Phase A–D: NLP & Carbon Intelligence)
- Natural language activity parsing with spaCy NLP pipeline
- IPCC-aligned carbon emission factors database (food, transport, energy, appliances)
- AI Coach with conversational carbon guidance
- OCR multimodal activity recognition (receipt scanning)
- IoT sensor architecture (stub)

### Added (Phase E–J: Frontend, Backend, Database & Auth)
- Next.js 14 frontend with dark/light theme, TailwindCSS
- FastAPI backend with async SQLAlchemy and PostgreSQL
- JWT authentication with access + refresh token rotation
- Dashboard, Analytics, Weekly Footprint, Category Breakdown
- Activity History with pagination
- Gamification: achievements, streaks, daily quests
- AI Recommendations and personalized coaching
- Profile management with avatar upload
- Marketplace for sustainable products

### Added (Phase K: Stability & Hardening)
- Circuit breakers on all external service calls
- Rate limiting per user per endpoint
- In-memory fallback cache for offline operation
- Database connection pooling and retry logic
- Safe DB wrapper with read-only degraded mode

### Added (Phase 7–10: Database, Reliability, Security, Performance)
- Production async SQLAlchemy engine with pool_size=20
- GZip compression middleware
- HTTP security headers middleware
- Content Security Policy
- Dynamic Next.js lazy loading (14 components)
- Next.js Image optimization for LCP
- React hooks ordering fixes

---

## Versioning Policy

| Version | Meaning |
|---|---|
| `MAJOR` (X.0.0) | Breaking API changes, major architecture redesign |
| `MINOR` (1.X.0) | New features, backward-compatible |
| `PATCH` (1.1.X) | Bug fixes, security patches |

**Next planned releases:**
- `v1.2.0` — Redis cache activation, Kafka message queue
- `v1.3.0` — Admin dashboard full UI, RBAC enforcement
- `v2.0.0` — Multi-tenant support, enterprise SSO
