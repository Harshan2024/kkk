# Docker Dependency Report — CarbonTracker AI

**Date:** 2026-07-11  
**Audit Scope:** Multi-stage image build context, package retention, and installation audits.  
**Release Target:** v1.0.0  
**Status:** ✅ CERTIFIED / IMAGE COMPLIANT  

---

## 1. Multi-Stage Dependency Lifecycle

The multi-stage backend [Dockerfile](file:///c:/Users/tutyr/Downloads/Harshan/New/backend/Dockerfile) handles package compilation and isolation cleanly:

- **Stage 1 (Builder stage):**
  - Base: `python:3.12-slim`
  - Installs compilation dependencies (`gcc`, `libpq-dev`).
  - Copies `requirements.txt`.
  - Runs `pip install --prefix=/install -r requirements.txt`. Both `asyncpg` and `aiosqlite` are compiled and installed into `/install` context.
- **Stage 2 (Runtime stage):**
  - Base: `python:3.12-slim`
  - Installs lightweight runtime libraries only (`libpq5`, `curl`).
  - Copies the pre-compiled packages context from builder: `COPY --from=builder /install /usr/local`.
  - Downloads the spaCy NLP model: `RUN python -m spacy download en_core_web_sm --quiet`.

---

## 2. Container Dependency Inventory

All required libraries are loaded into the final runtime container layer without compiling tools (`gcc` is dropped), keeping the final build footprint optimized.
