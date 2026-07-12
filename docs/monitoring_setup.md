# CarbonTracker AI — Production Monitoring Setup

**Date:** 2026-07-12  
**Status:** 📊 SETUP COMPLETED  

---

## 1. Centralized Logging Configuration

FastAPI is configured with standardized logging formats to separate normal request flow from runtime errors:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app_production.log")
    ]
)
```

---

## 2. Sentry Crash Reporting Setup
To capture unhandled frontend/backend errors in production, integrate Sentry initialization inside the root files:
-   **Backend (`main.py`)**:
    ```python
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1
    )
    ```
-   **Frontend (`app/layout.tsx`)**:
    Installs `@sentry/nextjs` to capture hydration client failures or unhandled promise exceptions dynamically.
