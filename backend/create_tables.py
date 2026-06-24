"""
create_tables.py -- CarbonTracker Table Creation Script (Phase I.1)
===================================================================
Standalone script that imports all SQLAlchemy models and calls
Base.metadata.create_all() to create any missing tables in PostgreSQL.

SAFE TO RE-RUN -- create_all() is idempotent: it will not drop or modify
tables that already exist. Only new tables are created.

Usage:
    cd backend
    .venv\\Scripts\\python.exe create_tables.py
"""
import sys
import os
import time

# Force UTF-8 output on Windows to avoid cp1252 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import engine, Base, OFFLINE_MODE

# -- Import ALL models to register them with Base.metadata --------------------
# Phase A-H (existing, locked)
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
# Phase I.1 (new)
from app.models.activity_entity import ActivityEntity
from app.models.history import History
from app.models.analytics import Analytics
from app.models.coach_report import CoachReport

# Phase I.4 (new)
from app.models.user_sustainability_profile import UserSustainabilityProfile
from app.models.goal import Goal
from app.models.trend_record import TrendRecord



def create_all_tables() -> None:
    """Create all registered tables in PostgreSQL. Idempotent."""
    if OFFLINE_MODE:
        print("ERROR: Database is in OFFLINE_MODE (no DATABASE_URL configured).")
        print("       Set DATABASE_URL in backend/.env and re-run.")
        sys.exit(1)

    print("=" * 60)
    print("CarbonTracker -- Phase I.1 Table Creation")
    print("=" * 60)
    print(f"Database: {str(engine.url).split('@')[-1]}")  # Hide credentials
    print()

    # List tables that Base knows about
    registered = sorted(Base.metadata.tables.keys())
    print(f"Registered tables ({len(registered)}):")
    for t in registered:
        print(f"  * {t}")
    print()

    print("Creating tables (idempotent -- existing tables are skipped)...")
    t_start = time.perf_counter()

    try:
        Base.metadata.create_all(bind=engine)
        elapsed = (time.perf_counter() - t_start) * 1000
        print(f"[OK] create_all() completed in {elapsed:.1f}ms")
    except Exception as e:
        print(f"[FAIL] create_all() FAILED: {e}")
        sys.exit(1)

    # -- Safe migration: add Phase I.1 columns to existing `users` table ------
    # The users table may already exist from an earlier phase without these cols.
    print()
    print("Running safe column migration for `users` table...")
    from sqlalchemy import inspect as sa_inspect, text as sql_text
    inspector = sa_inspect(engine)
    if "users" in inspector.get_table_names():
        existing_cols = {col["name"] for col in inspector.get_columns("users")}
        new_user_cols = {
            "xp":         "INTEGER NOT NULL DEFAULT 0",
            "level":      "INTEGER NOT NULL DEFAULT 1",
            "updated_at": "TIMESTAMP WITHOUT TIME ZONE",
            "redeemed_rewards": "JSON NULL",
            "email":           "VARCHAR(255) NULL UNIQUE",
            "hashed_password":  "VARCHAR(255) NULL",
            "is_active":        "BOOLEAN NOT NULL DEFAULT TRUE",
            "is_verified":      "BOOLEAN NOT NULL DEFAULT FALSE",
            "role":             "VARCHAR(50) NOT NULL DEFAULT 'user'",
            "last_login":       "TIMESTAMP WITHOUT TIME ZONE NULL",
        }
        with engine.connect() as conn:
            for col_name, col_def in new_user_cols.items():
                if col_name not in existing_cols:
                    try:
                        conn.execute(sql_text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                        conn.commit()
                        print(f"  [ADDED] users.{col_name}")
                    except Exception as e:
                        print(f"  [WARN]  Could not add users.{col_name}: {e}")
                else:
                    print(f"  [SKIP]  users.{col_name} already exists")

    # Safe migration for ai_insights columns
    print()
    print("Running safe column migration for `ai_insights` table...")
    if "ai_insights" in inspector.get_table_names():
        existing_insight_cols = {col["name"] for col in inspector.get_columns("ai_insights")}
        new_insight_cols = {
            "insight_type": "VARCHAR(100)",
            "priority": "VARCHAR(50)",
            "confidence": "DOUBLE PRECISION",
            "user_relevance_score": "DOUBLE PRECISION",
        }
        with engine.connect() as conn:
            for col_name, col_def in new_insight_cols.items():
                if col_name not in existing_insight_cols:
                    try:
                        conn.execute(sql_text(f"ALTER TABLE ai_insights ADD COLUMN {col_name} {col_def}"))
                        conn.commit()
                        print(f"  [ADDED] ai_insights.{col_name}")
                    except Exception as e:
                        print(f"  [WARN]  Could not add ai_insights.{col_name}: {e}")
                else:
                    print(f"  [SKIP]  ai_insights.{col_name} already exists")

    # Verify tables exist in DB
    print()
    print("Verifying tables in PostgreSQL...")
    inspector2 = sa_inspect(engine)
    existing = sorted(inspector2.get_table_names())

    phase_tables = [
        "users",
        "activities",
        "activity_entities",
        "history",
        "analytics",
        "coach_reports",
        "user_sustainability_profiles",
        "goals",
        "trend_records"
    ]

    all_present = True
    for table in phase_tables:
        if table in existing:
            print(f"  [OK]     {table}")
        else:
            print(f"  [MISS]   {table}  <- MISSING")
            all_present = False

    print()
    if all_present:
        print("[OK] All tables verified successfully.")

        print()
        print("You can now view them in pgAdmin:")
        print("  carbontracker -> Schemas -> public -> Tables")
    else:
        print("[FAIL] One or more tables are missing. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    create_all_tables()
