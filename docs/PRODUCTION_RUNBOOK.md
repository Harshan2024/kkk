# CarbonTracker AI — Production Runbook

**Version:** 1.1.0 | **Audience:** On-call Engineers | **Date:** 2026-07-05

---

> [!IMPORTANT]
> This runbook covers common operational procedures. For disaster recovery, see [DISASTER_RECOVERY_GUIDE.md](./DISASTER_RECOVERY_GUIDE.md).

---

## Quick Reference

| Endpoint | Purpose |
|---|---|
| `GET /api/system/status` | Public health check (no auth) |
| `GET /health` | Lightweight heartbeat |
| `GET /observability/metrics` | Full system metrics |
| `GET /api/v1/admin/health-dashboard` | Traffic-light dashboard |
| `GET /api/health/database` | DB-specific health |
| `GET /api/health/ai` | AI subsystem health |

---

## 1. Monitoring Checks

### Check System Status
```bash
curl https://api.carbontracker.ai/api/system/status | python -m json.tool
# Expected: { "status": "success", "data": { "backend": "online", "database": "online" } }
```

### Check Full Health Dashboard
```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.carbontracker.ai/api/v1/admin/health-dashboard | python -m json.tool
```

### Check Metrics
```bash
curl https://api.carbontracker.ai/observability/metrics | python -m json.tool
```

---

## 2. Alert Response Procedures

### 🔴 CRITICAL: Backend Offline

**Symptoms:** `/api/system/status` returns connection refused or 5xx

**Steps:**
1. Check process: `systemctl status carbontracker-backend` or `docker-compose ps`
2. Check logs: `docker-compose logs --tail=100 backend`
3. Restart backend: `docker-compose restart backend`
4. Wait 45 seconds for health check to pass
5. Verify: `curl http://localhost:8001/api/system/status`
6. If still failing, check environment variables and database connectivity

### 🔴 CRITICAL: Database Offline

**Symptoms:** `{ "database": "offline" }` in system status

**Steps:**
1. Check DB connectivity: `pg_isready -h $DB_HOST -p 5432 -U carbontracker`
2. Check DB process: `docker-compose ps db`
3. Restart DB: `docker-compose restart db` (wait 30s for startup)
4. Check DB logs: `docker-compose logs --tail=50 db`
5. Backend will auto-recover within 30 seconds (circuit breaker resets)
6. Verify: `curl http://localhost:8001/api/health/database`

> **Note:** Backend runs in READ_ONLY degraded mode when DB is offline. Existing data remains accessible. New writes are blocked.

### 🟡 WARNING: High Error Rate

**Symptoms:** `error_rate_pct` > 5% on key endpoints in metrics

**Steps:**
1. Identify failing endpoint from `/observability/metrics`
2. Check structured logs: `grep "ERROR" logs/carbontracker.log | tail -50`
3. Check for rate limit hits: look for `rate_limit_hits` counter spike
4. If NLP-related: check spaCy model health
5. If AI-related: check `ai_failures` counter; consider disabling AI temporarily

### 🟡 WARNING: High Memory Usage

**Symptoms:** `memory_pct` > 85% in health dashboard

**Steps:**
1. Check process memory: `ps aux | grep uvicorn`
2. Restart backend to clear memory: `docker-compose restart backend`
3. Check for large request payloads (5MB limit should prevent this)
4. Consider increasing server RAM or reducing `max_overflow` in DB pool

### 🟡 WARNING: Circuit Breaker Opens

**Symptoms:** `circuit_breaker_opens` > 3 in metrics

**Steps:**
1. Check which circuit breaker: look for `circuit_breaker` in logs
2. Allow 60 seconds for auto-reset (half-open state)
3. If database CB: follow Database Offline procedure
4. If AI CB: AI features may be temporarily degraded; NLP still works

---

## 3. Routine Operations

### Daily Backup
```bash
# Run daily backup
python backend/scripts/backup.py --schedule daily

# Verify backup was created
python backend/scripts/backup.py --list
```

### Weekly Backup
```bash
python backend/scripts/backup.py --schedule weekly
```

### Log Rotation
```bash
# Dry run first (preview)
python backend/scripts/log_rotate.py --dry-run

# Execute
python backend/scripts/log_rotate.py
```

### Database Migration / Schema Sync
```bash
# Schema syncs automatically on startup via create_all + sync_database_schema
# To manually trigger:
docker-compose exec backend python -c "
from app.database.session import engine, Base, sync_database_schema
Base.metadata.create_all(bind=engine)
sync_database_schema(engine)
print('Schema sync complete')
"
```

---

## 4. Deployment Procedure

### Zero-Downtime Deployment (Docker)

```bash
# 1. Pull latest code
git pull origin main

# 2. Build new images (while old ones are running)
docker-compose build --no-cache backend frontend

# 3. Restart with new images (brief downtime <10s)
docker-compose up -d backend frontend

# 4. Verify health
sleep 30
curl http://localhost:8001/api/system/status
```

### Rollback Procedure

```bash
# Roll back to previous Docker image
docker-compose down
docker-compose up -d --no-build  # Uses cached previous layers

# OR: Roll back via Git
git revert HEAD
docker-compose build backend frontend
docker-compose up -d
```

---

## 5. Log Access

### Structured Logs (JSON)
```bash
# Recent logs
tail -f logs/carbontracker.log | python -m json.tool

# Filter by level
cat logs/carbontracker.log | python -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('level') in ('ERROR', 'CRITICAL'):
            print(json.dumps(e, indent=2))
    except: pass
"

# Filter by endpoint
grep '\"endpoint\": \"/api/v1/auth/login\"' logs/carbontracker.log
```

### Request Log Analysis
```bash
# Top slowest endpoints
cat logs/carbontracker.log | python -c "
import sys, json
from collections import defaultdict
slow = []
for line in sys.stdin:
    try:
        e = json.loads(line)
        ctx = e.get('context', {})
        if 'duration_ms' in ctx:
            slow.append((ctx['duration_ms'], ctx.get('endpoint')))
    except: pass
for ms, ep in sorted(slow, reverse=True)[:10]:
    print(f'{ms:>8.1f}ms  {ep}')
"
```

---

## 6. User Support Operations

### Reset User Password (Admin)
```bash
# Via backend admin API (when implemented in v1.3.0)
# Currently: direct database update
docker-compose exec db psql -U carbontracker carbontracker -c "
UPDATE users SET hashed_password = '<bcrypt_hash>' WHERE email = 'user@example.com';
"
```

### Unlock Rate-Limited IP
```bash
# Rate limiter is in-memory — restart backend to clear
docker-compose restart backend
```
