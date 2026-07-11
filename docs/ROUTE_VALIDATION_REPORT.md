# Route Validation Report — CarbonTracker AI

**Date:** 2026-07-11  
**Audit Scope:** Route verification comparisons, prefix settings, and endpoint checks.  
**Release Target:** v1.0.0  
**Status:** ✅ CERTIFIED / NO DUPLICATIONS  

---

## 1. Serviced Route Registry Map

Below is the verified routing map comparison between `app.routes` and serviced endpoints:

- **Root API Namespace:** `/api/v1`
  - `/api/v1/auth/register` (POST) — User Registration
  - `/api/v1/auth/login` (POST) — Credentials Verification
  - `/api/v1/auth/refresh` (POST) — Token Rotation
  - `/api/v1/auth/logout` (POST) — Revocation / Blacklist
  - `/api/v1/profile` (GET, PUT) — User Profile & XP updates
  - `/api/v1/activities` (GET, POST) — Activity log & calculations
  - `/api/v1/analytics` (GET) — Footprint aggregates
  - `/api/v1/insights` (GET) — AI insights feed
  - `/api/v1/chat` (POST) — AI Copilot chat
  - `/api/v1/recommendations` (GET) — Carbon actions list
  - `/api/v1/achievements` (GET) — User badges status

- **observability & Health endpoints:**
  - `/health` (GET) — Lightweight connection check
  - `/api/health` (GET) — Detailed dependency audit
  - `/api/system/status` (GET) — Core online diagnostics
  - `/observability/metrics` (GET) — Prometheus status counts

- **Documentation mounts:**
  - `/docs` (GET) — Swagger UI console
  - `/openapi.json` (GET) — OpenAPI specs document

---

## 2. Integrity Checks
- **Shadowed / Unreachable Routes:** Checked prefix layouts. All route calls resolve correctly.
- **Duplicated paths:** Verified that `api_router` and `auth_router` are only included once in `main.py` under the `/api/v1` prefix boundary.
