# CarbonTracker AI — Docker Setup Guide

**Version:** 1.1.0 | **Date:** 2026-07-05

---

## Architecture

Docker Compose orchestrates four containers:

```
┌─────────────────────────────────────────────┐
│              Docker Network                  │
│                                             │
│  ┌──────────┐   ┌──────────┐   ┌────────┐  │
│  │  Nginx   │   │ Frontend │   │Backend │  │
│  │  :80     │──▶│  :3000   │   │ :8001  │  │
│  │  :443    │──▶│          │──▶│        │  │
│  └──────────┘   └──────────┘   └────┬───┘  │
│                                     │       │
│                               ┌─────▼───┐  │
│                               │PostgreSQL│  │
│                               │  :5432   │  │
│                               └──────────┘  │
└─────────────────────────────────────────────┘
```

---

## Prerequisites

- Docker Engine 24+
- Docker Compose v2+
- 2GB+ RAM
- Ports 80, 443, 3000, 8001 available

---

## Quick Start (Development)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/carbontracker.git
cd carbontracker

# 2. Copy env template (development mode)
cp backend/.env.development backend/.env

# 3. Start all services (no SSL in dev)
docker-compose up -d db backend frontend

# 4. Check health
curl http://localhost:8001/api/system/status

# 5. Open app
open http://localhost:3000
```

---

## Production Deployment

### Step 1: Configure Environment

```bash
# Copy production template
cp backend/.env.production backend/.env

# Edit with real values
nano backend/.env
```

Required values to set:
```env
DATABASE_URL=postgresql://USER:PASS@db:5432/carbontracker?sslmode=prefer
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
ENVIRONMENT=production
```

### Step 2: Configure SSL Certificates

Place your SSL certificates in `nginx/ssl/`:
```bash
mkdir -p nginx/ssl
# Option A: Let's Encrypt (recommended)
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# Option B: Self-signed (for testing only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

### Step 3: Build and Start

```bash
# Build all images
docker-compose build --no-cache

# Start all services
docker-compose up -d

# Verify all containers are healthy
docker-compose ps

# Expected output:
# carbontracker-db         running (healthy)
# carbontracker-backend    running (healthy)
# carbontracker-frontend   running (healthy)
# carbontracker-nginx      running
```

---

## Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a single service
docker-compose restart backend

# Rebuild after code change
docker-compose build backend
docker-compose up -d backend

# Enter a container shell
docker-compose exec backend bash
docker-compose exec db psql -U carbontracker carbontracker

# Stop all services
docker-compose down

# Stop and remove volumes (DANGER: deletes all data)
docker-compose down -v
```

---

## Database Management

```bash
# Run database backup
docker-compose exec backend python scripts/backup.py --schedule daily

# Restore from backup
docker-compose exec backend python scripts/restore.py --latest daily

# Connect to database directly
docker-compose exec db psql -U carbontracker carbontracker

# View database logs
docker-compose logs db
```

---

## Health Checks

All services include Docker health checks:

| Service | Health Check | Interval | Retries |
|---|---|---|---|
| `db` | `pg_isready` | 10s | 5 |
| `backend` | `GET /api/system/status` | 30s | 3 |
| `frontend` | `GET /` | 30s | 3 |

Check health status:
```bash
docker inspect --format='{{json .State.Health}}' carbontracker-backend | python -m json.tool
```

---

## Docker Image Details

### Backend Image

| Layer | Base | Size |
|---|---|---|
| Builder | `python:3.12-slim` | ~200MB |
| Runtime | `python:3.12-slim` | ~350MB total |

- Non-root user (`carbontracker`, uid 1001)
- spaCy model pre-installed (`en_core_web_sm`)
- 2 uvicorn workers
- Health check on `/api/system/status`

### Frontend Image

| Layer | Base | Size |
|---|---|---|
| Deps | `node:20-alpine` | ~400MB |
| Builder | `node:20-alpine` | Build only |
| Runtime | `node:20-alpine` | ~150MB total |

- Non-root user (`carbontracker`, uid 1001)
- Next.js standalone output
- No npm at runtime

---

## Volumes

| Volume | Used By | Contains |
|---|---|---|
| `postgres_data` | db | All database data |
| `backend_static` | backend, nginx | Avatar uploads, static files |
| `backend_logs` | backend | Application log files |

---

## Resource Limits (Recommended)

Add to `docker-compose.yml` per service:
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: "0.5"
    reservations:
      memory: 256M
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Backend fails to start | Check `DATABASE_URL` is correct in `.env` |
| `Address already in use` | Kill existing processes: `lsof -ti:8001 \| xargs kill` |
| Frontend can't reach backend | Ensure `NEXT_PUBLIC_API_URL` is set correctly |
| SSL error on HTTPS | Check `nginx/ssl/` contains valid certificates |
| Database connection refused | Wait 30s for PostgreSQL to fully start |
| `spacy model not found` | Rebuild backend image: `docker-compose build backend` |
