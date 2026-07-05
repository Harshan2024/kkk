# CarbonTracker AI — Disaster Recovery Guide

**Version:** 1.1.0 | **RTO:** 2 hours | **RPO:** 24 hours | **Date:** 2026-07-05

---

> [!CAUTION]
> This guide covers scenarios involving data loss risk or complete service failure. Follow each step precisely. Always verify backups before restoring.

---

## Recovery Objectives

| Metric | Target |
|---|---|
| **RTO** (Recovery Time Objective) | ≤ 2 hours |
| **RPO** (Recovery Point Objective) | ≤ 24 hours (daily backup) |
| **Backup Frequency** | Daily (automated) |
| **Backup Retention** | Daily: 7, Weekly: 4, Monthly: 12 |

---

## Scenario 1: Complete Application Failure

**Signs:** All endpoints return 5xx or connection refused

### Recovery Steps

```bash
# 1. Check container status
docker-compose ps

# 2. Restart all services
docker-compose restart

# 3. If containers won't start, rebuild
docker-compose build --no-cache
docker-compose up -d

# 4. Verify recovery
curl http://localhost:8001/api/system/status

# 5. Check database
docker-compose exec db pg_isready -U carbontracker carbontracker
```

**Expected recovery time:** 5–15 minutes

---

## Scenario 2: Database Corruption / Data Loss

> [!CAUTION]
> This will overwrite the current database. Ensure you are restoring the correct backup.

### Step 1: Identify most recent valid backup

```bash
python backend/scripts/backup.py --list

# Output example:
# Schedule   Timestamp                Size         File
# ─────────────────────────────────────────────────────────────
# daily      2024-07-04_03-00-00      24.5 MB   ✅ carbontracker.dump
# daily      2024-07-03_03-00-00      23.8 MB   ✅ carbontracker.dump
```

### Step 2: Verify backup integrity

```bash
python backend/scripts/restore.py --verify \
  --file backups/daily/2024-07-04_03-00-00_carbontracker.dump

# Expected: [VERIFY] ✅ Backup is valid. Contains N table(s).
```

### Step 3: Stop backend (prevent writes during restore)

```bash
docker-compose stop backend
```

### Step 4: Restore database

```bash
python backend/scripts/restore.py \
  --file backups/daily/2024-07-04_03-00-00_carbontracker.dump \
  --yes
```

### Step 5: Restart backend and verify

```bash
docker-compose start backend
sleep 30
curl http://localhost:8001/api/system/status
```

**Expected recovery time:** 15–45 minutes depending on database size

---

## Scenario 3: Server Failure / VPS Migration

### Step 1: Provision new server

- Ubuntu 22.04 LTS recommended
- Minimum: 2 vCPU, 4GB RAM, 40GB SSD

### Step 2: Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo apt-get install -y docker-compose-plugin
```

### Step 3: Restore application

```bash
# Clone repository
git clone https://github.com/your-org/carbontracker.git
cd carbontracker

# Copy environment (from backup or secrets manager)
cp backend/.env.production backend/.env
# Edit with production values

# Copy backup files from old server or S3
scp -r old-server:/path/to/backups ./backups

# Start services
docker-compose up -d db
sleep 30  # Wait for PostgreSQL startup

# Restore database
python backend/scripts/restore.py --latest daily --yes

# Start remaining services
docker-compose up -d
```

### Step 4: Update DNS

Change DNS A record to point to new server IP.
Allow up to 24 hours for DNS propagation.

**Expected recovery time:** 60–120 minutes

---

## Scenario 4: Secret Key Compromise (JWT Token Breach)

> [!CAUTION]
> Rotating the secret key invalidates ALL existing sessions. All users must log in again.

### Steps

```bash
# 1. Generate new secret key
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Update SECRET_KEY in environment
# Render/Railway: update in dashboard and redeploy
# Docker: update backend/.env and restart

# 3. Restart backend (all existing tokens immediately invalidated)
docker-compose restart backend

# 4. Notify users via email that they need to log in again
# (use admin notification or email list)
```

**Expected impact:** All users logged out. No data loss.
**Expected recovery time:** 5 minutes

---

## Scenario 5: Data Exfiltration

**Signs:** Unusual query patterns, unauthorized admin access, bulk data export

### Immediate Actions

```bash
# 1. IMMEDIATELY rotate SECRET_KEY (see Scenario 4)
# This invalidates all existing tokens

# 2. Take application offline temporarily
docker-compose stop backend frontend

# 3. Capture forensic evidence
docker-compose logs --no-color backend > incident_logs_$(date +%Y%m%d).txt

# 4. Reset database user passwords
docker-compose exec db psql -U carbontracker -c "ALTER USER carbontracker PASSWORD 'new_strong_password';"

# 5. Update DATABASE_URL with new password
# 6. Review audit logs for scope of access
grep "ADMIN" backend/logs/audit.log | tail -100

# 7. Restart services
docker-compose up -d
```

---

## Backup Strategy

### Automated Schedule (via cron)

Add to server crontab (`crontab -e`):

```cron
# Daily backup at 3:00 AM UTC
0 3 * * * cd /path/to/carbontracker && python backend/scripts/backup.py --schedule daily >> logs/backup.log 2>&1

# Weekly backup every Sunday at 4:00 AM UTC
0 4 * * 0 cd /path/to/carbontracker && python backend/scripts/backup.py --schedule weekly >> logs/backup.log 2>&1

# Monthly backup on 1st of month at 5:00 AM UTC
0 5 1 * * cd /path/to/carbontracker && python backend/scripts/backup.py --schedule monthly >> logs/backup.log 2>&1

# Log rotation daily at 2:00 AM UTC
0 2 * * * cd /path/to/carbontracker && python backend/scripts/log_rotate.py >> logs/rotation.log 2>&1
```

### Off-Site Backup (Recommended)

Copy daily backups to S3 or cloud storage:

```bash
# Add to backup.py output pipeline or create a separate script
aws s3 cp backups/daily/ s3://carbontracker-backups/daily/ --recursive
```

---

## Recovery Verification Checklist

After any recovery scenario, verify:

- [ ] `GET /api/system/status` returns `"backend": "online"` and `"database": "online"`
- [ ] Login works: `POST /api/v1/auth/login`
- [ ] Activity logging works: `POST /api/v1/activities`
- [ ] Analytics returns data (not empty)
- [ ] Audit logs are being written
- [ ] Backups resume on schedule
