# Production Bug Tracker — CarbonTracker AI

**Version:** 1.0.0  
**Date:** 2026-07-07  
**Status:** ✅ 100% RESOLVED / ZERO ACTIVE BLOCKED DEFECTS  

---

## 1. Executive Status
This bug tracker maintains a history of issues identified during the system audit and verification stages of testing. No new bugs have been identified during the Phase 17 PAT run. All P0 (Critical) and P1 (High) issues from previous development phases have been successfully resolved and verified.

---

## 2. Defects Log

| Bug ID | Description | Severity | Phase Identified | Status | Verification Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-001** | Next.js SSR build ReferenceError: sessionStorage is not defined | P0 - Critical | Phase 16.1 | ✅ Resolved | Replaced bare `sessionStorage` references with guarded `window.sessionStorage` logic inside components. Verified in successful `npm run build`. |
| **BUG-002** | Temporal Dead Zone (TDZ) ReferenceError on `checkServerRestart` | P0 - Critical | Phase 16.1 | ✅ Resolved | Relocated `checkServerRestart` callback declaration before `fetchSystemHealth` inside `aiStore.tsx`. Verified in clean production build. |
| **BUG-003** | Unicode arrow character output crashes PowerShell verification script | P3 - Low | Phase 17 | ✅ Resolved | Script runner configured to initialize with `PYTHONIOENCODING="utf-8"`. Script runs and returns output correctly. |

---

## 3. Defect Classification Definitions

### Critical (P0) - Release Blocker
- Application crashes, data corruption, auth validation bypasses, or deployment compilation failures.

### High (P1) - Release Blocker
- Incorrect emissions calculation metrics, broken core layout loops, or failed route transitions.

### Medium (P2) - Non-Blocker
- Minor performance lag, warning logs, or non-optimal network payload sizes.

### Low (P3) - Non-Blocker
- Typographical anomalies, minor visual margins discrepancies, or debug print statements.
