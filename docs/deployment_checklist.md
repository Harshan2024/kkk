# CarbonTracker AI — Production Deployment Checklist

**Status:** ✅ CERTIFIED READY FOR CI/CD STABILIZATION

Use this checklist to deploy the backend, frontend, and database services to production safely.

---

## Pre-Deployment Verification
- [x] Run `pytest` inside `backend/` and confirm 100% test pass status.
- [x] Run `npx tsc --noEmit` inside `frontend/` to confirm zero typescript compilation errors.
- [x] Search the codebase to ensure no `localhost` or `127.0.0.1` endpoints exist in the frontend client.

---

## 1. Database Setup (Neon PostgreSQL)
- [ ] Initialize a production database branch on Neon.
- [ ] Retrieve the secure `DATABASE_URL` string (e.g., `postgresql://...`).
- [ ] Run the migration script or initial table creations:
  ```bash
  python -m app.create_tables
  ```
- [ ] Confirm index creation for performance optimization:
  - `idx_activities_user_id`
  - `idx_activities_logged_at`

---

## 2. Backend Service Deployment (Render / Docker)
- [ ] Create a new **Web Service** on Render linking your repository branch.
- [ ] Select environment type: **Docker**.
- [ ] Configure Environment Variables:
  - `DATABASE_URL` = (production Neon database URL)
  - `JWT_SECRET` = (secure random string)
  - `CORS_ORIGINS` = `https://carbontracker.vercel.app` (your vercel url)
  - `FORECAST_ENABLED` = `false` (set to `true` once Prophet environment compiles)
- [ ] Verify healthcheck endpoint path: `/api/v1/system/health`.

---

## 3. Frontend Service Deployment (Vercel)
- [ ] Link your repository to a new project on Vercel.
- [ ] Set build command: `npm run build`.
- [ ] Set output directory: `.next`.
- [ ] Configure Environment Variables:
  - `NEXT_PUBLIC_API_URL` = (your Render Web Service live URL)
- [ ] Confirm deployment build passes and routes load without console warnings.
