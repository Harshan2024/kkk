# API Audit Report — CarbonTracker AI

**Date:** 2026-07-08  
**Audit Scope:** REST API Schema Compliance, HTTP Response Codes, and Timeout Resiliency.  
**Release Target:** v1.0.0  
**Status:** ✅ CERTIFIED / CONTRACT-COMPLIANT  

---

## 1. Schema & Validation Standards

Every REST route endpoint complies with the strict Pydantic model schemas defined in the backend configuration:

- **JSON Envelopes:** Public endpoints return structured envelopes:
  - Success format: `{"status": "success", "data": {...}}`
  - Error format: `{"detail": "..."}` or `{"status": "error", "message": "..."}`
- **Validation Codes:** Inputs failing schemas return `422 Unprocessable Entity` with details specifying the target field path.
- **Unauthorized Requests:** Endpoints requiring auth enforce token validation. Missing/invalid credentials return `401 Unauthorized`.

---

## 2. API Resilience & Timeout Audit

- **Execution Timeout limits:** All API routes enforce internal AbortController signals to abort long-running requests after **15 seconds** (or 30s for the AI chat endpoint), avoiding hanging client threads.
- **Failover / Degradation States:**
  - If PostgreSQL is offline, `/api/system/status` returns `database: offline` with a `success` status wrapper, letting the frontend render a user-friendly "Database Reconnecting" warning bar.
  - The API does not crash or leak internal raw system logs under network timeouts.
