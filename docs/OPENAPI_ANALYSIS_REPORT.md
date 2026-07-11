# OpenAPI Analysis Report — CarbonTracker AI

**Date:** 2026-07-11  
**Audit Scope:** Route registration maps, /openapi.json mapping, and FastAPI definitions.  
**Release Target:** v1.0.0  
**Status:** ✅ RESOLVED / SCHEMAS VALIDATED  

---

## 1. Investigation Findings

- **Issue:** `/openapi.json` returned `404 Not Found` in previous runs.
- **Root Cause:** The uvicorn listener process was running a stale code instance that had registered `openapi_url` at `/api/v1/openapi.json` (consistent with legacy config settings), meaning standard root-level `/openapi.json` requests were naturally rejected.
- **Resolution:** Re-instantiated FastAPI using:
  ```python
  app = FastAPI(
      title="CarbonTracker API",
      version="1.4.0",
      docs_url="/docs",
      redoc_url="/redoc",
      openapi_url="/openapi.json",
      lifespan=lifespan
  )
  ```
  We terminated the stale backend worker. The newly started uvicorn server successfully listens to `/openapi.json` at root level.

---

## 2. API Contract Check

We verified `/openapi.json` returns HTTP `200 OK` and outputs valid OpenAPI 3.1.0 JSON specs:
```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "CarbonTracker API",
    "version": "1.4.0"
  },
  "paths": {
    "/api/v1/activities/parse": { ... }
  }
}
```
Schemas correspond exactly to Pydantic definitions.
