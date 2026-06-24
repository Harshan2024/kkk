# app/models/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Central model registry — import ALL SQLAlchemy models here so that
# Base.metadata.create_all() discovers every table on startup.
# ─────────────────────────────────────────────────────────────────────────────

# Phase A–H models (original, locked)
from app.models.models import (
    User,
    Category,
    EmissionFactor,
    Activity,
    SustainabilityScore,
    Achievement,
    AIInsight,
    ChatMessage,
    UserCorrection,
)

# Phase I.1 models (new tables)
from app.models.activity_entity import ActivityEntity
from app.models.history import History
from app.models.analytics import Analytics
from app.models.coach_report import CoachReport

# Phase I.4 models
from app.models.user_sustainability_profile import UserSustainabilityProfile
from app.models.goal import Goal
from app.models.trend_record import TrendRecord

__all__ = [
    # Existing
    "User",
    "Category",
    "EmissionFactor",
    "Activity",
    "SustainabilityScore",
    "Achievement",
    "AIInsight",
    "ChatMessage",
    "UserCorrection",
    # New — Phase I.1
    "ActivityEntity",
    "History",
    "Analytics",
    "CoachReport",
    # New — Phase I.4
    "UserSustainabilityProfile",
    "Goal",
    "TrendRecord",
]
