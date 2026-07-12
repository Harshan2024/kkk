# CarbonTracker AI — Observability Report

**Date:** 2026-07-12  
**Status:** 📊 OBSERVABILITY ACTIVE

---

## 1. System Health Endpoint

The system status monitor checks core microservices and database state every 30 seconds:
-   **URL**: `GET /api/v1/system/health`
-   **Response Format**:
    ```json
    {
      "status": "online",
      "database": "online",
      "cache": "active",
      "ai_engine": "online",
      "failed": false
    }
    ```

---

## 2. Resource Utilization Metrics

Observability logs record container utilization characteristics to prevent memory leak crashes:
-   **Container CPU Limit**: Max 80% under standard traffic.
-   **Database Connections Pool**: Tracks active pool connections, highlighting warnings if connections exceed 15 concurrent pools.
-   **Cache Hit Rate**: Logs hit/miss statuses for local caches to maintain <50ms response bounds.
