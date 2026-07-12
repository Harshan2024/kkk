# CarbonTracker AI — Bug Tracking Dashboard

**Date:** 2026-07-12  
**Status:** ✅ ALL RELEASE BUGS RESOLVED  

---

## 1. Release Bug Status

| Bug ID | Component | Description | Priority | Assigned | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-001** | Backend | CORS Preflight OPTIONS returned 400 Bad Request | Critical | DevOps | Resolved |
| **BUG-002** | Docker | Tailwind module missing in standalone build stage | High | DevOps | Resolved |
| **BUG-003** | Sanitizer| Windows backslash path traversal test failed in CI | High | Backend | Resolved |
| **BUG-004** | UI | AI calculation results disappeared after 1-2s | Medium | Frontend | Resolved |
| **BUG-005** | UI | Profile initials initial load hydration mismatch | Low | Frontend | Resolved |

---

## 2. Resolutions Log
-   **CORS Options Fix**: Updated middlewares in `main.py` to act as pass-throughs when `request.method == "OPTIONS"`.
-   **Tailwind Docker Fix**: Refactored `frontend/Dockerfile` to compile using full dependencies (production + development).
-   **Sanitizer Windows Fix**: Normalizes backward slashes to forward slashes before splitting the filename path.
-   **Disappearing Results Fix**: Used global store `activities[0]` as the single source of truth for the latest logged card detail.
