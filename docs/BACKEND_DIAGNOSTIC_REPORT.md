# Backend Diagnostic Report — CarbonTracker AI

**Date:** 2026-07-11  
**Audit Scope:** Process Identification, Stale Process Detection, and Uvicorn Lifecycles.  
**Release Target:** v1.0.0  
**Status:** ✅ RESOLVED / SINGLE INSTANCE REGISTERED  

---

## 1. Process & Environment Diagnostics

- **Listening Port 8001:** Analyzed processes listening on port 8001 via Windows TCP connection utility:
  ```powershell
  Get-NetTCPConnection -LocalPort 8001 | Format-List -Property OwningProcess, State
  ```
  - Identified Process ID (PID): **13672**
  - Process Owner: Uvicorn main worker
  - Process Status: `Listen`
- **Orphan / Duplicate Processes:** No secondary or duplicate process listeners exist on port 8001. All duplicate processes have been successfully terminated.
- **Python Executable:** Serves using the isolated python context at `c:\Users\tutyr\Downloads\Harshan\New\.venv\Scripts\python.exe`.
- **Working Directory:** Confirmed root `c:\Users\tutyr\Downloads\Harshan\New\backend`.
- **Startup Entrypoint:** Uvicorn targets `app.main:app` correctly.
