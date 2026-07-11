# Dependency Audit Report — CarbonTracker AI

**Date:** 2026-07-11  
**Audit Scope:** Database driver dependencies, runtime safety verification, and environment checks.  
**Release Target:** v1.0.0  
**Status:** ✅ RESOLVED / DEPENDENCIES RESOLVED  

---

## 1. Updated Dependencies Registry

To ensure full compatibility with dynamic hosting environments (such as Render) and support SQLAlchemy async sessions, we updated [requirements.txt](file:///c:/Users/tutyr/Downloads/Harshan/New/backend/requirements.txt) to explicitly list the asynchronous PostgreSQL and SQLite drivers:

- **asyncpg**: Installed version `0.31.0` (production database async driver).
- **aiosqlite**: Installed version `0.22.1` (development/testing database async fallback driver).

---

## 2. Python 3.12 Virtual Environment Status

All primary runtime and development packages resolve with zero warnings or package collisions:

| Library | Version | Dialect Scope | Verified |
| :--- | :--- | :--- | :--- |
| **fastapi** | `0.136.1` | REST Engine Framework | Yes |
| **uvicorn** | `0.47.0` | ASGI Web Server | Yes |
| **sqlalchemy** | `2.0.49` | Core SQL engine & connection mapping | Yes |
| **psycopg2-binary**| `2.9.12` | PostgreSQL (Sync Driver) | Yes |
| **asyncpg** | `0.31.0` | PostgreSQL (Async Driver) | Yes |
| **aiosqlite** | `0.22.1` | SQLite (Async Driver) | Yes |
| **spacy** | `3.7.4` | NLP parser & text analytics | Yes |
