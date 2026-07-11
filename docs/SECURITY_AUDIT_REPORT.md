# Security Audit Report — CarbonTracker AI

**Date:** 2026-07-08  
**Audit Scope:** HTTP Headers, Injection Protections, Rate Limiters, and CORS Policies.  
**Release Target:** v1.0.0  
**Status:** ✅ CERTIFIED / SECURE  

---

## 1. Network & Header Compliance

HTTP Security Headers are validated on all public API endpoints:

```http
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
Cross-Origin-Opener-Policy: same-origin-allow-popups
Cross-Origin-Resource-Policy: same-origin
Content-Security-Policy: default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline' ...
```

- **CORS Configuration:** Enforces strict origin matching. Restricts requests to allowed production domains.
- **CSP Controls:** Blocks cross-site scripting by allowing only explicitly trusted source domains.

---

## 2. Attack Mitigation Audits

- **SQL Injection (SQLi) Audit:** Parameterized ORM queries prevent input strings from altering query operations. Tested against SQL payloads (`' OR 1=1 --`), which are safely stored as literal strings.
- **Cross-Site Scripting (XSS) Audit:** Inputs are sanitized. HTML symbols (`<` and `>`) are converted to safe character codes (`&lt;` and `&gt;`). Script schemes (`javascript:`) are removed.
- **Directory Traversal Audit:** Filename sanitizer strips null bytes (`\x00`) and parent markers (`../`). `../../../etc/passwd` correctly resolves to the clean basename `passwd`.
- **Brute Force Protection:** Enforces endpoint rate limiting on `/api/v1/auth/login`. Concurrent login requests return `429 Too Many Requests`.
