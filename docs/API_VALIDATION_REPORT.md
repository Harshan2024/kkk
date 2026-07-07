# API Validation Report — CarbonTracker AI

**Version:** 1.0.0  
**Date:** 2026-07-07  
**Status:** ✅ CERTIFIED / CONTRACT-COMPLIANT  

---

## 1. Scope
Validation of all core REST backend API endpoints to ensure they follow exact JSON contracts, response envelopes, error structures, rate-limiting rules, and timeout parameters under load.

---

## 2. API Endpoint Matrix

| Method | Endpoint | Description | Auth Required | Envelope Format | Validated |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/register` | User signup | No | `{"status": "success", "data": {...}}` | Yes |
| **POST** | `/api/v1/auth/login` | Credentials authentication | No | `{"status": "success", "data": {"access_token": "...", "refresh_token": "..."}}` | Yes |
| **POST** | `/api/v1/auth/refresh` | Token rotation | No | `{"access_token": "...", "refresh_token": "..."}` | Yes |
| **POST** | `/api/v1/auth/logout` | Token revocation/blacklist | No | `{"status": "success"}` | Yes |
| **GET** | `/api/v1/profile` | Load user profile / level / XP | Yes | `{"username": "...", "email": "...", "xp": ...}` | Yes |
| **GET** | `/api/v1/dashboard/summary` | Today/Weekly emissions, budget, streaks, quests | Yes | `{"today_emissions": ..., "weekly_emissions": ...}` | Yes |
| **POST** | `/api/v1/activities` | Log activity (NLP text) | Yes | `{"id": ..., "input_text": "...", "category": "..."}` | Yes |
| **GET** | `/api/v1/activities` | Paginated activity history list | Yes | `[{"id": ..., "input_text": "..."}]` | Yes |
| **GET** | `/api/v1/analytics` | Emissions history, groupings, and ratings | Yes | `{"daily": {...}, "weekly": {...}, "monthly": {...}}` | Yes |
| **GET** | `/api/v1/insights` | AI-generated green tips and priority weights | Yes | `[{"id": ..., "content": "..."}]` | Yes |
| **POST** | `/api/v1/chat` | AI Copilot query handler | Yes | `{"response": "..."}` | Yes |
| **GET** | `/api/system/status` | Public health check | No | `{"status": "success", "data": {"backend": "online"}}` | Yes |
| **GET** | `/observability/metrics` | System counters and metrics | No | `{"collected_at": "...", "system": {...}}` | Yes |

---

## 3. Resilience & Validation Checks

### Invalid Input / Malformed Payload
- Tested POST payload with incorrect schemas on `/api/v1/auth/register`.
- Result: Correctly rejected with `422 Unprocessable Entity` containing explicit Pydantic verification details.

### Missing/Expired Authentication
- Tested GET request to `/api/v1/profile` without `Authorization` header.
- Result: Returned `401 Unauthorized` with `{"detail": "Not authenticated"}`.
- Tested request with expired JWT token.
- Result: Returned `401 Unauthorized` with `{"detail": "Token has expired"}`.

### Rate Limiting & 429 Validation
- Tested high-concurrency requests to `/api/v1/auth/login`.
- Result: Endpoint successfully throttled requests using the Redis-ready rate limiter, returning `429 Too Many Requests`.

---

## 4. Certification
All REST endpoints adhere exactly to the defined API contract schemas. No schema leaks or uncaught JSON serialization errors were observed.
