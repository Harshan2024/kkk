# Authentication Audit Report — CarbonTracker AI

**Date:** 2026-07-08  
**Audit Scope:** JWT Lifecycles, Token Rotation, Session Bounding, and Role-Based Authorization.  
**Release Target:** v1.0.0  
**Status:** ✅ CERTIFIED / PRODUCTION-READY  

---

## 1. Token Cryptography & Rotation

- **Hash Standard:** Password storage uses `bcrypt` hashing with salt rounds. Raw passwords are never stored.
- **JWT Signatures:** Tokens are signed using HMAC SHA-256 (`HS256`). Signature keys are read from production environment variables.
- **Token Expiry limits:**
  - Access Token: `15 minutes`
  - Refresh Token: `7 days`
- **Rotation Validation:** Calling `/api/v1/auth/refresh` rotates the token pair and blacklists the previous refresh token to prevent reuse.

---

## 2. Session Bounding & Dev Policy Checks

We verified the new Development Authentication Policy implementation:

- **Enforced Session Bounding:** Authentication storage uses `window.sessionStorage`. Closing the tab/window discards the tokens automatically.
- **Refreshes (F5):** Navigating in the same session retains access via sessionStorage states.
- **Cache Invalidation:** Initializing the application purges local HTTP state caches.
- **Server Restart Detection:** Uptime drift checker evaluates metrics on port 8001. A boot time shift of > 10s forces an immediate client logout to align local caches.
- **Role-Based Access Control (RBAC):** Access to admin routes (e.g. `/api/v1/admin/health-dashboard`) requires `admin` role claims, returning `403 Forbidden` if validation fails.
