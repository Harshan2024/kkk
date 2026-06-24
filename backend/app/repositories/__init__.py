# app/repositories/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Repository layer — provides CRUD operations for all Phase I.1 models.
# ─────────────────────────────────────────────────────────────────────────────
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.coach_repository import CoachRepository

__all__ = [
    "UserRepository",
    "ActivityRepository",
    "HistoryRepository",
    "AnalyticsRepository",
    "CoachRepository",
]
