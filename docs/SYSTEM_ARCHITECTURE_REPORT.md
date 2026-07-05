# CarbonTracker AI — System Architecture Report

**Version:** 1.1.0 | **Date:** 2026-07-05 | **Status:** Production

---

## Executive Summary

CarbonTracker AI is a full-stack, AI-powered sustainability platform that enables users to track their carbon footprint through natural language activity parsing, receive personalized AI coaching, and visualize their environmental impact through rich analytics.

The system is designed for **high availability**, **horizontal scalability**, and **enterprise-grade observability** using a modern microservice-ready architecture.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Client Layer                                   │
│  ┌───────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │  Web Browser      │   │  Mobile (PWA)    │   │  Admin Panel     │  │
│  │  Next.js 14 App   │   │  Service Worker  │   │  /admin page     │  │
│  └────────┬──────────┘   └────────┬─────────┘   └────────┬─────────┘  │
└───────────┼─────────────────────────────────────────────────────────────┘
            │ HTTPS
┌───────────▼─────────────────────────────────────────────────────────────┐
│                       Nginx Reverse Proxy                               │
│  • TLS 1.2/1.3 termination    • Gzip compression                       │
│  • Rate limiting (30 rpm API, 5 rpm auth)   • Security headers          │
│  • Static file serving         • API routing (/api/* → backend)        │
└───────────┬─────────────────────────────────────────────────────────────┘
            │
  ┌─────────┴──────────┐
  │                    │
  ▼                    ▼
┌──────────────────┐  ┌──────────────────────────────────────────────────┐
│   Frontend        │  │            Backend (FastAPI)                     │
│   Next.js 14      │  │                                                  │
│   Port 3000       │  │  ┌──────────────────────────────────────────┐   │
│                   │  │  │  Middleware Stack (ordered)               │   │
│   Components:     │  │  │  1. Request ID injection                  │   │
│   • Dashboard     │  │  │  2. Security headers (HSTS, CSP, etc.)   │   │
│   • Analytics     │  │  │  3. XSS payload scanner                   │   │
│   • AI Coach      │  │  │  4. Request timing + metrics recording   │   │
│   • History       │  │  │  5. GZip compression                     │   │
│   • Profile       │  │  └───────────────┬──────────────────────────┘   │
│   • Marketplace   │  │                  │                               │
│   • Admin         │  │  ┌───────────────▼──────────────────────────┐   │
│                   │  │  │  Router Layer                             │   │
│   State:          │  │  │  • /api/v1/auth/*    (AuthRouter)        │   │
│   • zustand       │  │  │  • /api/v1/*         (APIRouter)         │   │
│   • ThemeStore    │  │  │  • /api/system/*     (System endpoints)  │   │
│   • AIStore       │  │  │  • /observability/*  (Metrics)           │   │
│                   │  │  │  • /api/v1/admin/*   (Admin)             │   │
│   Perf:           │  │  └───────────────┬──────────────────────────┘   │
│   • Dynamic       │  │                  │                               │
│     imports (14)  │  │  ┌───────────────▼──────────────────────────┐   │
│   • Next/Image    │  │  │  Service Layer                            │   │
│   • Code split    │  │  │  • AuthService      • ActivityService    │   │
│                   │  │  │  • CarbonCalcEngine • AnalyticsService   │   │
└──────────────────┘  │  │  • AICoachService   • GamificationSvc   │   │
                       │  │  • RecommendationSvc • ProfileService    │   │
                       │  └───────────────┬──────────────────────────┘   │
                       │                  │                               │
                       │  ┌───────────────▼──────────────────────────┐   │
                       │  │  Data Access Layer                        │   │
                       │  │  • SQLAlchemy ORM (sync + async)         │   │
                       │  │  • Repository pattern                     │   │
                       │  │  • Safe DB wrapper (read-only fallback)  │   │
                       │  │  • Connection pool: size=20, overflow=40 │   │
                       │  └───────────────┬──────────────────────────┘   │
                       │                  │                               │
                       │  ┌───────────────▼──────────────────────────┐   │
                       │  │  Cross-Cutting Concerns                   │   │
                       │  │  • Circuit breakers (5 services)         │   │
                       │  │  • Rate limiter (per-user per-endpoint)  │   │
                       │  │  • In-process cache (Redis-ready)        │   │
                       │  │  • Task queue (RabbitMQ/Kafka-ready)     │   │
                       │  │  • Audit logger (structured JSON)        │   │
                       │  │  • Notification dispatcher               │   │
                       │  └──────────────────────────────────────────┘   │
                       │  Port 8001                                       │
                       └──────────────────────────────────────────────────┘
                                          │
                       ┌──────────────────▼──────────────────────────────┐
                       │          Data Layer                             │
                       │                                                 │
                       │  ┌────────────────┐  ┌────────────────────┐   │
                       │  │  PostgreSQL 16 │  │  In-Memory Cache   │   │
                       │  │  (Primary DB)  │  │  (Redis-ready)     │   │
                       │  │               │  │                    │   │
                       │  │  Tables:      │  │  Keys:             │   │
                       │  │  • users      │  │  • dashboard:*     │   │
                       │  │  • activities │  │  • analytics:*     │   │
                       │  │  • goals      │  │  • profile:*       │   │
                       │  │  • achievements│  │  • leaderboard:*  │   │
                       │  │  • chat_msgs  │  └────────────────────┘   │
                       │  │  • emission_  │                            │
                       │  │    factors    │  ┌────────────────────┐   │
                       │  └───────────────┘  │  Task Queue        │   │
                       │                     │  (In-Process now,  │   │
                       │                     │   RabbitMQ/Kafka   │   │
                       │                     │   ready)           │   │
                       │                     └────────────────────┘   │
                       └─────────────────────────────────────────────────┘
```

---

## Component Inventory

### Frontend Components (Next.js 14)

| Component | Type | Lazy | Description |
|---|---|---|---|
| `page.tsx` | Page | — | Main dashboard shell + tab router |
| `WeeklyFootprintChart` | Widget | ✅ | Recharts area chart for 7-day footprint |
| `CategoryDonutChart` | Widget | ✅ | Recharts donut for emission category breakdown |
| `CarbonCharts` | Widget | ✅ | Multi-chart analytics dashboard |
| `ActivityHistory` | Widget | ✅ | Paginated activity log (5/page) |
| `AIRecommendations` | Widget | ✅ | Personalized sustainability tips |
| `Achievements` | Widget | ✅ | Gamification badges and streaks |
| `CoachDashboard` | Widget | ✅ | AI Coach conversation interface |
| `IoTDashboard` | Widget | ✅ | Smart home sensor panel (stub) |
| `DailyQuests` | Widget | ✅ | Daily sustainability challenges |
| `StreakFooter` | Widget | ✅ | Streak counter and calendar |
| `Marketplace` | Widget | ✅ | Sustainable products catalog |
| `Settings` | Widget | ✅ | User preferences and notifications |
| `CopilotChat` | Widget | ✅ | Floating AI chat copilot |
| `HabitInsights` | Widget | ✅ | Behavioral habit analysis |
| `EarthPanel` | Component | — | 3D Earth visualization (Next/Image) |
| `admin/page.tsx` | Page | — | System health monitoring admin panel |

### Backend Services (FastAPI)

| Module | Purpose |
|---|---|
| `app/main.py` | Application bootstrap, middleware stack, health endpoints |
| `app/api/endpoints.py` | All 80+ API endpoint definitions |
| `app/auth/` | JWT service, auth service, RBAC, password service |
| `app/nlp/parser.py` | spaCy NLP activity parser |
| `app/carbon/` | Emission calculation engine |
| `app/ai/` | AI coach, embeddings, OCR, orchestrator |
| `app/analytics/` | Carbon trend analysis |
| `app/gamification/` | Achievements, quests, streaks |
| `app/utils/` | Metrics, logger, notifier, cache, circuit_breaker, rate_limiter, sanitizer |
| `app/cache/redis_adapter.py` | Redis-ready cache adapter |
| `app/queue/task_queue.py` | Message queue abstraction |

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend Framework | Next.js | 14.2 |
| Frontend Language | TypeScript | 5.4 |
| UI Library | React | 18.3 |
| Charting | Recharts | 2.12 |
| Animation | Framer Motion | 11 |
| Styling | TailwindCSS | 3.4 |
| Backend Framework | FastAPI | 0.110+ |
| Backend Language | Python | 3.12 |
| ORM | SQLAlchemy | 2.0 |
| Database | PostgreSQL | 16 |
| NLP | spaCy | 3.7 |
| Auth | PyJWT + bcrypt | 2.8 / 4.1 |
| Web Server | Uvicorn | 0.28+ |
| Reverse Proxy | Nginx | 1.25 |
| Containerization | Docker + Compose | Latest |
| CI/CD | GitHub Actions | — |

---

## Security Architecture

- **Authentication:** JWT access tokens (30 min) + refresh tokens (7 days) with rotation
- **Authorization:** Role-based (user / moderator / admin / super_admin)
- **Transport:** HTTPS via Nginx TLS 1.2/1.3, HSTS enforced
- **Headers:** HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Rate Limiting:** 5 req/min auth, 30 req/min general API
- **Input Sanitization:** XSS escaping, path traversal blocking on all user inputs
- **Audit Logging:** All auth events logged in structured JSON (credentials never logged)

---

## Data Flow: Activity Logging

```
User types "I drove 15km to work"
        ↓
Frontend → POST /api/v1/activities { text: "..." }
        ↓
Sanitizer.sanitize_text() → clean text
        ↓
NLP Parser (spaCy) → entities: [{type: transport, value: 15km}]
        ↓
Carbon Calculator → emission: 2.85 kg CO2e
        ↓
Database → INSERT activities
        ↓
Gamification → check achievements → update streak
        ↓
Task Queue → enqueue recalculate_analytics job (async)
        ↓
Response → { activities, emission_kg, score_delta }
        ↓
Frontend → update dashboard charts
```
