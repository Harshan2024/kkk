# Dependency Audit Report — CarbonTracker AI

**Date:** 2026-07-11  
**Audit Scope:** Production and Development dependency verification.  
**Release Target:** v1.0.0  
**Status:** ✅ CERTIFIED / ENVIRONMENT COMPLETE  

---

## 1. Package Status Verification

All core python libraries are installed in the virtual environment `c:\Users\tutyr\Downloads\Harshan\New\.venv`:

| Library | Version | Status | Verification Note |
| :--- | :--- | :--- | :--- |
| **fastapi** | `0.136.1` | ✅ Verified | Core router API engine |
| **uvicorn** | `0.47.0` | ✅ Verified | ASGI server process |
| **sqlalchemy** | `2.0.49` | ✅ Verified | Connection pool & ORM |
| **psycopg2-binary**| `2.9.12` | ✅ Verified | PostgreSQL driver |
| **asyncpg** | `0.31.0` | ✅ Verified | Async PostgreSQL driver |
| **PyJWT** | `2.13.0` | ✅ Verified | Token signature & security |
| **bcrypt** | `4.1.2` | ✅ Verified | Secure password hashing |
| **python-multipart**| `0.0.9` | ✅ Verified | Multipart file uploads |
| **pydantic** | `2.6.4` | ✅ Verified | Schemas validation |
| **spacy** | `3.7.4` | ✅ Verified | Spacy NLP engine |
| **aiosqlite** | `0.20.0` | ✅ Verified | Async SQLite test driver |
| **pytest** | `9.1.1` | ✅ Verified | Testing suite framework |
| **locust** | `2.44.4` | ✅ Verified | Load testing framework |

---

## 2. Integrity Checks
- **circular Imports:** verified with static analysis tool. None detected.
- **version Compatibility:** Checked library releases. No compatibility warnings raised during server process startup.
