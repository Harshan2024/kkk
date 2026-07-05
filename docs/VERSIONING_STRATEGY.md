# CarbonTracker AI — Versioning Strategy

**Version:** 1.1.0 | **Date:** 2026-07-05

---

## Semantic Versioning

CarbonTracker AI follows [Semantic Versioning 2.0.0](https://semver.org/).

**Format:** `MAJOR.MINOR.PATCH`

| Component | Triggers | Examples |
|---|---|---|
| **MAJOR** | Breaking API changes, major architecture redesign | `1.0.0 → 2.0.0` |
| **MINOR** | New features, backward-compatible additions | `1.0.0 → 1.1.0` |
| **PATCH** | Bug fixes, security patches, performance improvements | `1.1.0 → 1.1.1` |

---

## Version History

| Version | Date | Highlights |
|---|---|---|
| `1.1.0` | 2026-07-05 | Phase 11–15: Observability, Testing, Docker, Ops, Scalability |
| `1.0.0` | 2026-07-02 | Initial production release (Phase A–K + Phase 7–10) |

---

## Pre-release Naming

```
1.2.0-alpha.1    ← Alpha: early development, unstable
1.2.0-beta.1     ← Beta: feature complete, testing
1.2.0-rc.1       ← Release candidate: ready for production review
1.2.0             ← Stable release
```

---

## Version Bumping Procedure

### For a Patch Release (Bug Fix)

```bash
# Update version in all locations
VERSION="1.1.1"

# Backend
echo "VERSION = '$VERSION'" > backend/app/version.py

# Frontend
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" frontend/package.json

# Changelog — add entry under [Unreleased]
# Commit and tag
git add -A
git commit -m "chore: bump version to $VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin main --tags
```

### For a Minor Release (New Feature)

Same procedure as patch, plus:
1. Update `CHANGELOG.md` with all new features under `## [X.Y.0]`
2. Create a GitHub Release from the tag
3. Update deployment documentation if needed

### For a Major Release (Breaking Change)

1. Create a migration guide (`docs/MIGRATION_vX.0.md`)
2. Announce deprecation of old API endpoints (minimum 60-day notice)
3. Update all API versioning in URLs (`/api/v1/` → `/api/v2/`)
4. Update OpenAPI documentation

---

## API Versioning

All API routes are versioned via URL path:

```
/api/v1/auth/login       ← Current stable
/api/v2/auth/login       ← Future (when breaking changes needed)
```

**Policy:**
- Old versions are maintained for **minimum 6 months** after a new version launches
- Deprecated endpoints return `X-Deprecated: true` header and a sunset date
- No API breakage without MAJOR version bump

---

## Where Version is Declared

| File | Variable | Purpose |
|---|---|---|
| `backend/app/version.py` | `VERSION = "1.1.0"` | Python source of truth |
| `frontend/package.json` | `"version": "1.1.0"` | npm package version |
| `CHANGELOG.md` | `## [1.1.0] — ...` | Release changelog |
| Docker images | `LABEL version="1.1.0"` | Container metadata |

---

## Release Checklist

Before any release:

- [ ] All tests passing in CI
- [ ] CHANGELOG.md updated with all changes
- [ ] Version bumped in `version.py` and `package.json`
- [ ] Docker images built and tested
- [ ] Staging deployment verified
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Git tag created and pushed

---

## Planned Roadmap

| Version | ETA | Features |
|---|---|---|
| `v1.1.1` | 2026-Q3 | Security patch if CVEs found |
| `v1.2.0` | 2026-Q3 | Redis cache activation, Kafka message queue |
| `v1.3.0` | 2026-Q4 | Admin dashboard full UI, RBAC enforcement frontend |
| `v2.0.0` | 2027-Q1 | Multi-tenant, enterprise SSO, API v2 |
