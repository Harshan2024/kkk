# CarbonTracker AI — Deployment Guide

**Version:** 1.1.0 | **Date:** 2026-07-05

---

## Overview

CarbonTracker AI can be deployed to:
- **Frontend:** Vercel (recommended) or any Node.js host
- **Backend:** Render, Railway, Fly.io, or any Python/Docker host
- **Database:** Neon, Supabase, Render PostgreSQL, or self-hosted PostgreSQL 16

---

## Option A: Vercel + Render (Recommended for Production)

### Step 1: Database — Neon PostgreSQL

1. Create a free account at [neon.tech](https://neon.tech)
2. Create a new project: `carbontracker-production`
3. Copy the connection string (pooled endpoint):
   ```
   postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require&channel_binding=require
   ```
4. Save this as `DATABASE_URL`

### Step 2: Backend — Render

1. Go to [render.com](https://render.com) → New Web Service
2. Connect your GitHub repository
3. Configure:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3.12
   - **Build Command:** `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables:
   ```
   DATABASE_URL=<neon-connection-string>
   SECRET_KEY=<64-char-random-key>
   ENVIRONMENT=production
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   OPENAI_API_KEY=<your-key>
   ```
5. Under **Health Check Path:** set `/api/system/status`
6. Deploy

> **Generate SECRET_KEY:**
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### Step 3: Frontend — Vercel

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import your GitHub repository
3. Configure:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
4. Set environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```
5. Deploy

### Step 4: Update Backend CORS

In Render environment variables, add:
```
BACKEND_CORS_ORIGINS=https://your-app.vercel.app
```

Restart the Render service.

### Step 5: Verify

```bash
# Check backend health
curl https://your-backend.onrender.com/api/system/status

# Expected:
# { "status": "success", "data": { "backend": "online", "database": "online" } }
```

---

## Option B: Railway

### Backend on Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Add environment variables in the Railway dashboard (same as Render above)
3. Railway auto-detects the Python app and deploys

### Database on Railway

1. Add a PostgreSQL plugin to your Railway project
2. Railway auto-sets `DATABASE_URL` — no manual configuration needed

---

## Option C: Docker Compose (Self-Hosted / VPS)

See [DOCKER_SETUP.md](./DOCKER_SETUP.md) for full instructions.

### Quick start:

```bash
# Clone repo
git clone https://github.com/your-org/carbontracker.git
cd carbontracker

# Configure production environment
cp backend/.env.production backend/.env

# Edit backend/.env with your actual values
nano backend/.env

# Start all services
docker-compose up -d

# Check health
curl http://localhost:8001/api/system/status
```

---

## Environment Variables Reference

### Backend (required)

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db?sslmode=require` |
| `SECRET_KEY` | JWT signing secret (64+ chars) | `abc123...` (random hex) |
| `ENVIRONMENT` | Runtime environment | `production` |

### Backend (optional)

| Variable | Default | Description |
|---|---|---|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | JWT refresh token lifetime |
| `OPENAI_API_KEY` | — | OpenAI API (for advanced AI features) |
| `REDIS_URL` | — | Enable Redis cache |
| `RABBITMQ_URL` | — | Enable RabbitMQ task queue |
| `ALERT_SLACK_WEBHOOK_URL` | — | Slack alert webhook |
| `ALERT_MIN_LEVEL` | `error` | Minimum alert level (`info`/`warning`/`error`/`critical`) |

### Frontend

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |

---

## Post-Deployment Checklist

- [ ] `GET /api/system/status` returns `{ "backend": "online", "database": "online" }`
- [ ] Login works end-to-end
- [ ] Activity logging saves to database
- [ ] Dashboard charts load
- [ ] HTTPS is enforced (HTTP redirects to HTTPS)
- [ ] CSP headers present in browser DevTools → Network → Response Headers
- [ ] Service Worker registered (DevTools → Application → Service Workers)

---

## Scaling Recommendations

| Traffic | Configuration |
|---|---|
| < 1,000 users/day | Render free tier + Neon free tier |
| 1,000–10,000 users/day | Render paid + Neon pro |
| 10,000–100,000 users/day | Railway + Redis cache + read replicas |
| > 100,000 users/day | Kubernetes + multi-region + Kafka |
