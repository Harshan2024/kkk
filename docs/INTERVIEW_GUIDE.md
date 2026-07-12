# CarbonTracker AI — Interview Preparation Guide

This guide compiles typical technical interview questions and architectural highlights for recruiters and technical reviewers.

---

## 1. Top Core Interview Questions

### Q1: How does the natural-language logging feature work?
**Answer**: When a user inputs text, the frontend sends it to `/api/v1/activity` in real-time or on submit. The backend feeds the string into a spaCy NLP pipeline that utilizes token regex matcher matching to extract units, values, and entities. Once matched, it references standard databases (IPCC/DEFRA) to calculate total carbon values and inserts the activity record into PostgreSQL.

### Q2: How did you fix the CORS preflight blocker?
**Answer**: Starlette decorator-defined HTTP middlewares wrap the application outermost and execute *before* Starlette's `CORSMiddleware`. As a result, browser preflight `OPTIONS` requests would fail custom security middlewares (like XSS or timing) and return errors before reaching `CORSMiddleware`. To fix this, we modified the custom middlewares to bypass all checks and immediately return empty pass-throughs when `request.method == "OPTIONS"`.

### Q3: Why did you implement a multi-stage Docker build?
**Answer**: Next.js requires devDependencies (like TailwindCSS and TypeScript) to run `next build` at build time. If we run `npm ci --only=production`, the compiler fails due to missing modules. Our multi-stage configuration:
1.  Installs **all** packages (including devDependencies) to perform compilation.
2.  Performs `npm run build`.
3.  Copies only Next.js standalone folder output (which contains traced production modules) to the runtime image.

### Q4: How is database scaling and rollback safety handled?
**Answer**: We use async PostgreSQL drivers (`asyncpg`) and configure pool limitations (`pool_size=20`, `max_overflow=10`). Scoped SQLAlchemy session contexts wrap writes in transactional blocks, guaranteeing complete rollback execution on database network interruptions.
