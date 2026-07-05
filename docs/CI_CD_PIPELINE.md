# CarbonTracker AI — CI/CD Pipeline Documentation

**Version:** 1.1.0 | **Date:** 2026-07-05 | **Phase:** 13

---

## Pipeline Overview

The GitHub Actions CI/CD pipeline automatically runs on every push to `main`, `develop`, and `staging` branches, and on all pull requests to `main` and `staging`.

### Pipeline Stages

```
Push / PR
    │
    ▼
┌─────────────────┐
│ backend-lint     │  ← Syntax check + flake8 (parallel)
└────────┬────────┘
         │
    ┌────▼────────────────┐   ┌─────────────────────┐
    │ backend-tests        │   │ frontend-build       │
    │ (unit + integration) │   │ (lint + Next.js build)│
    └────────┬────────────┘   └──────────┬───────────┘
             │                           │
             └──────────┬────────────────┘
                        │
               ┌────────▼────────┐
               │  docker-build   │  ← Both images built
               └────────┬────────┘
                        │
               ┌────────▼────────┐
               │ security-scan   │  ← pip-audit + npm audit
               └─────────────────┘
```

---

## Job Details

### Job 1: `backend-lint`
**Runs on:** `ubuntu-latest`
**Duration:** ~2 minutes

| Step | Command | Blocking |
|---|---|---|
| Python setup | `setup-python@v5` | Yes |
| flake8 (style) | `flake8 app/ --max-line-length=120` | No (warnings only) |
| Syntax check | `python -m py_compile app/main.py` + key modules | Yes |

---

### Job 2: `backend-tests`
**Runs on:** `ubuntu-latest`
**Depends on:** `backend-lint`
**Services:** PostgreSQL 16 (ephemeral)
**Duration:** ~5 minutes

| Step | Command | Blocking |
|---|---|---|
| Python setup | `setup-python@v5` | Yes |
| Install deps | `pip install -r requirements.txt` | Yes |
| spaCy model | `python -m spacy download en_core_web_sm` | Yes |
| Unit tests | `pytest tests/unit/ --junit-xml=...` | Yes |
| Integration tests | `pytest tests/integration/ ...` | No (may require full DB) |
| Upload results | `actions/upload-artifact@v4` | No |

**Environment:**
```yaml
DATABASE_URL: postgresql://test_user:test_password@localhost:5432/carbontracker_test
SECRET_KEY: ci-test-secret-key-for-github-actions-only
ENVIRONMENT: test
```

---

### Job 3: `frontend-build`
**Runs on:** `ubuntu-latest`
**Parallel with:** `backend-tests`
**Duration:** ~4 minutes

| Step | Command | Blocking |
|---|---|---|
| Node.js setup | `setup-node@v4 (v20)` | Yes |
| Install deps | `npm ci` | Yes |
| ESLint | `npm run lint` | No (warnings only) |
| Next.js build | `npm run build` | Yes |
| Upload build | `actions/upload-artifact@v4` | No |

---

### Job 4: `docker-build`
**Runs on:** `ubuntu-latest`
**Depends on:** `backend-tests` AND `frontend-build`
**Runs on:** Push events only (not PRs)
**Duration:** ~8 minutes (first run), ~3 minutes (cached)

| Step | Command | Blocking |
|---|---|---|
| Docker Buildx | `setup-buildx-action@v3` | Yes |
| Build Backend | `docker/build-push-action@v5` (push=false) | Yes |
| Build Frontend | `docker/build-push-action@v5` (push=false) | Yes |

Uses GitHub Actions cache (`type=gha`) for layer caching.

---

### Job 5: `security-scan`
**Runs on:** `ubuntu-latest`
**Depends on:** `backend-tests`
**Duration:** ~3 minutes

| Step | Tool | Blocking |
|---|---|---|
| Python deps | `pip-audit -r requirements.txt` | No (inform only) |
| npm deps | `npm audit --audit-level=high` | No (inform only) |

---

## Secrets Configuration

Add these in **GitHub → Settings → Secrets and Variables → Actions:**

| Secret | Used By | Description |
|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | deploy-production (future) | Render deploy webhook |
| `VERCEL_TOKEN` | deploy-production (future) | Vercel CLI token |

No secrets are required for the current 5-job pipeline.

---

## Branch Strategy

| Branch | Triggers | Result |
|---|---|---|
| `feature/*` | Push | Lint + tests only |
| `develop` | Push | Full pipeline (no deploy) |
| `staging` | Push + PR | Full pipeline |
| `main` | Push + PR | Full pipeline + deploy (when enabled) |

---

## Viewing Pipeline Results

1. Go to your GitHub repository
2. Click **Actions** tab
3. Select the workflow run
4. Click any job to see detailed step logs
5. Download test result artifacts from the **Artifacts** section

---

## Failing the Pipeline

The pipeline fails when:
- `python -m py_compile` finds a syntax error
- `pytest tests/unit/` fails (non-zero exit)
- `npm run build` fails

The pipeline passes with warnings when:
- flake8 reports style issues (non-blocking)
- ESLint reports warnings
- Integration tests fail (may need full DB setup)
- Security audit finds low/medium vulnerabilities

---

## Local Pipeline Simulation

Run the same checks locally before pushing:

```bash
# Backend lint
cd backend
flake8 app/ --max-line-length=120 --ignore=E501,W503 || true
python -m py_compile app/main.py

# Backend tests
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="local-test-key"
pytest tests/unit/ -v

# Frontend build
cd ../frontend
npm ci
npm run lint || true
npm run build
```
