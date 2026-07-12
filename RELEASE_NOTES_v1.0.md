# CarbonTracker AI — Release Notes v1.0.0

We are proud to announce the public release of **CarbonTracker AI Version 1.0.0**, a production-ready, high-performance personal carbon foot-printing and AI coaching application.

---

## 1. Key Features

### 1.1 Natural Language Processing & Carbon Engine
-   **spaCy-powered parsing**: Allows users to enter natural language activities like `"drove 18 km in my car"` or `"ate chicken biryani"` to calculate carbon emissions instantly.
-   **IPCC/DEFRA Mapped Dataset**: Accurate emission factors mapped across transport, food, electricity, appliances, waste, and shopping.
-   **Compound Activity parsing**: Splits compound sentences with `and` or commas to log multiple activities in a single submission.

### 1.2 Interactive Dashboard & Analytics
-   **Dynamic charts**: Visualizes weekly carbon footprints, category breakdown ratios (recharts), and trends.
-   **Gamification**: Integrates daily quests, achievements, streaks, and user XP level trackers.
-   **AI Sustainability Coach**: Conversational interface giving active tips on reducing footprints and interpreting eco scores.

### 1.3 Enterprise-Grade Security & Performance
-   **JWT Session Security**: Secure token authentication with access + refresh token rotation and router redirects.
-   **Clean Multi-Stage Containers**: Frontend and backend Docker images optimized for Render/Vercel.
-   **Observability**: Integrated healthchecks `/api/v1/system/health` and live resource utilization telemetry dashboards.
-   **High Concurrency Connection Pooling**: Scoped transaction isolation and rollback routines for Neon database operations.
