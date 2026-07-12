# CarbonTracker AI — API Verification Report

**Date:** 2026-07-12  
**Status:** ✅ VERIFIED & FULLY FUNCTIONAL  

---

## 1. Verified Endpoints Map

The following endpoints have been verified under automated test suites and live curl execution.

| Area | Route | Methods | Expected Status Code | Actual Status Code | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Auth** | `/api/v1/auth/register` | `POST` | `201 Created` | `201 Created` | Pass |
| **Auth** | `/api/v1/auth/login` | `POST` | `200 OK` | `200 OK` | Pass |
| **Auth** | `/api/v1/auth/refresh` | `POST` | `200 OK` | `200 OK` | Pass |
| **Dashboard**| `/api/v1/dashboard/summary`| `GET` | `200 OK` | `200 OK` | Pass |
| **Activities**| `/api/v1/activity` | `POST` | `201 Created` | `201 Created` | Pass |
| **Activities**| `/api/v1/activity/history`| `GET` | `200 OK` | `200 OK` | Pass |
| **Analytics**| `/api/v1/analytics` | `GET` | `200 OK` | `200 OK` | Pass |
| **Profile** | `/api/v1/profile` | `GET` / `PUT`| `200 OK` | `200 OK` | Pass |
| **AI Coach** | `/api/v1/ai/insight` | `GET` | `200 OK` | `200 OK` | Pass |
| **Uptime** | `/api/v1/system/health` | `GET` | `200 OK` | `200 OK` | Pass |

---

## 2. CORS Preflight & OPTIONS Middleware Passing
The backend CORS configuration has been hardened to prevent browser blocking:
-   **Preflight (OPTIONS)** requests immediately bypass XSS and security middlewares and return `200 OK` with correct header bindings.
-   **Allowed Origins**: Configured dynamically via `CORS_ORIGINS` to safely accept connections from Vercel domains (`https://*.vercel.app`) and local dev domains.

---

## 3. Database Resilience under Integration Tests
All unit tests and integration tests inside `backend/tests` pass successfully:
-   **Result**: 123 passed, 3 skipped.
-   **Warnings**: Deprecation warnings for legacy UTC time declarations are flagged but do not block execution.
