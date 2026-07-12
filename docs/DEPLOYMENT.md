# CarbonTracker AI — Deployment Specifications

**Status:** Ready for Staging/Production Deployment

---

## 1. Environment Configurations

Set the following environment keys on target platforms:

### 1.1 Backend Environment Variables
*   `DATABASE_URL`: Connection string to serverless Neon PostgreSQL.
*   `JWT_SECRET`: Random hash seed for access token encryption.
*   `CORS_ORIGINS`: Delimiter-separated list of allowed origins (e.g. `https://carbontracker.vercel.app`).
*   `PORT`: Dynamic port mapping (automatically configured by Render container runners).

### 1.2 Frontend Environment Variables
*   `NEXT_PUBLIC_API_URL`: Fully qualified production domain of the deployed FastAPI service (e.g., `https://your-backend.onrender.com`).

---

## 2. Docker Orchestration (Local & Standalone)
Use the included `docker-compose.yml` to launch local production simulations:
```bash
docker-compose up --build
```
This boots:
-   **PostgreSQL**: Configured with automated health checks.
-   **Backend**: Async FastAPI container listening on port `8001`.
-   **Frontend**: Standalone Next.js container listening on port `3000`.
-   **Nginx Proxy**: Acts as a reverse router directing requests to appropriate endpoints and blocking XSS traffic.
