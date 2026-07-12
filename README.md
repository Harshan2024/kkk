# CarbonTracker AI

CarbonTracker AI is an enterprise-grade personal carbon foot-printing, natural language parsing, and AI coaching platform designed to help individuals monitor, analyze, and offset their daily emissions.

---

## 1. Project Overview & Features
-   **Natural Language Logging**: Enter daily activities in plain English (e.g. `"drove 18 km in car"` or `"ate beef meal"`).
-   **Multi-Entity parsing**: Tokenizes compound activities to log multiple actions in one sentence.
-   **Lighthouse Verified UI**: React/Next.js dashboard utilizing glassmorphic styles, light/dark themes, and interactive charts (Recharts).
-   **Observability Console**: Real-time status indicator dashboards (/admin) tracking database pool socket health, latency, and logs.
-   **JWT Token Security**: High-security access + refresh token verification loops with router protections.

---

## 2. Tech Stack
-   **Frontend**: React, Next.js 14 (standalone output), TailwindCSS, Framer Motion, Lucide React.
-   **Backend**: Python, FastAPI, SQLAlchemy (Async), Uvicorn, spaCy NLP.
-   **Database**: PostgreSQL hosted on Neon.
-   **DevOps & Deployment**: Docker (multi-stage builds), Docker Compose, GitHub Actions, Nginx.

---

## 3. Folder Structure
```text
├── backend/            # FastAPI async server & unit tests
├── frontend/           # Next.js 14 client & Tailwind layouts
├── nginx/              # Production web reverse proxy configuration
├── docs/               # Architecture, API, and QA reports
├── docker-compose.yml  # Multi-container orchestrator
└── README.md           # This file
```

---

## 4. Quick Start & Local Installation

### Prerequisites
- Node.js 20+
- Python 3.12+
- Docker & Docker Compose (Optional)

### Step 1: Run Backend
1. Go to `backend/` and install packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Set Environment variables in `.env` (DATABASE_URL, JWT_SECRET).
3. Start FastAPI server:
   ```bash
   python -m uvicorn app.main:app --port 8001
   ```

### Step 2: Run Frontend
1. Go to `frontend/` and install packages:
   ```bash
   npm ci
   ```
2. Start Dev server:
   ```bash
   npm run dev -- --port 3001
   ```

---

## 5. Deployment Architecture
The production pipeline compiles Next.js standalone containers deployed on Vercel, communicates with Docker backend services on Render, and queries high-speed serverless PostgreSQL databases on Neon.
-   Frontend: Vercel
-   Backend API: Render
-   Database: Neon PostgreSQL
