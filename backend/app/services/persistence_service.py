"""
persistence_service.py -- CarbonTracker Persistence Service (Phase I.2)
=======================================================================
Thin helper that saves ActivityEntity, History, and Analytics rows after
an Activity has been committed. Called from background workers in endpoints.py.

Design decisions:
- Every step is wrapped in its own try/except so a failure in one step
  (e.g. entity insert) never aborts the history or analytics steps.
- All database operations go through Phase I.1 repositories.
- Does NOT modify Activity rows -- that is the caller's responsibility.
- Incremental analytics: recalculates weekly/monthly totals from DB
  aggregation in a single SQL query, not a full table scan.

Usage (inside a background worker that already has a db session):
    from app.services.persistence_service import save_activity_persistence
    save_activity_persistence(db, user_id, activity, parsed_part, metadata)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Activity
from app.repositories.activity_repository import ActivityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger("carbontracker.persistence")


def _calculate_carbon_totals(db: Session, user_id: int) -> tuple[float, float, float]:
    """
    Returns (weekly_total, monthly_total, sustainability_score) from a single
    aggregation query. Never raises -- returns (0.0, 0.0, 100.0) on failure.
    """
    try:
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        row = db.query(
            func.sum(Activity.calculated_value).filter(
                Activity.logged_at >= week_start
            ).label("weekly"),
            func.sum(Activity.calculated_value).filter(
                Activity.logged_at >= month_start
            ).label("monthly"),
        ).filter(Activity.user_id == user_id).first()

        weekly_total  = float(row.weekly  or 0.0)
        monthly_total = float(row.monthly or 0.0)

        # Sustainability score: 100 when weekly <= 21 kgCO2e (3/day), 0 when >= 105 (15/day)
        daily_avg = weekly_total / 7.0 if weekly_total > 0 else 0.0
        if daily_avg <= 3.0:
            score = 100.0
        elif daily_avg >= 15.0:
            score = 0.0
        else:
            score = 100.0 - ((daily_avg - 3.0) / 12.0) * 100.0

        return round(weekly_total, 4), round(monthly_total, 4), round(score, 2)
    except Exception as e:
        logger.error(f"[persistence_service] _calculate_carbon_totals failed for user={user_id}: {e}")
        return 0.0, 0.0, 100.0


def save_activity_persistence(
    db: Session,
    user_id: int,
    activity: Activity,
    parsed_part: dict,
    metadata: dict,
) -> None:
    """
    After an Activity row has been committed, persist:
      1. ActivityEntity row (one entity per parsed part)
      2. History row       (link user_id -> activity_id)
      3. Analytics upsert  (incremental weekly/monthly snapshot)

    Each step is individually protected -- failures are logged, never raised.

    Args:
        db:          Active SQLAlchemy session (caller owns lifecycle).
        user_id:     The owning user's id.
        activity:    The already-committed Activity ORM instance.
        parsed_part: The NLP-parsed dict for this activity (item, category, etc.)
        metadata:    The calculation metadata dict returned by calculate_emissions().
    """
    activity_id = getattr(activity, "id", None)
    if not activity_id:
        logger.warning("[persistence_service] save_activity_persistence called with un-persisted Activity (no id).")
        return

    # ── Step 1: ActivityEntity ────────────────────────────────────────────────
    try:
        entity_name     = parsed_part.get("item") or "unknown"
        entity_category = parsed_part.get("category") or "lifestyle"
        quantity        = float(parsed_part.get("quantity") or 1.0)
        unit            = parsed_part.get("unit") or "unit"
        # Emission factor from metadata (multiple key names in use across engines)
        factor = float(
            metadata.get("emission_factor")
            or metadata.get("factor")
            or parsed_part.get("factor")
            or parsed_part.get("food_co2_kg")
            or parsed_part.get("shopping_co2_kg")
            or 0.0
        )
        carbon_emission = float(activity.calculated_value or 0.0)

        act_repo = ActivityRepository(db)
        act_repo.create_entity(
            activity_id=activity_id,
            entity_name=entity_name,
            entity_category=entity_category,
            quantity=quantity,
            unit=unit,
            factor=factor,
            carbon_emission=carbon_emission,
        )
        logger.info(
            f"[persistence_service] ActivityEntity saved: activity_id={activity_id} "
            f"entity='{entity_name}' category='{entity_category}' "
            f"qty={quantity}{unit} carbon={carbon_emission:.4f} kgCO2e"
        )
    except Exception as e:
        logger.error(
            f"[persistence_service] ActivityEntity save FAILED for activity_id={activity_id}: {e}"
        )

    # ── Step 2: History ───────────────────────────────────────────────────────
    try:
        hist_repo = HistoryRepository(db)
        hist_repo.create(user_id=user_id, activity_id=activity_id)
        logger.info(
            f"[persistence_service] History row saved: user_id={user_id} activity_id={activity_id}"
        )
    except Exception as e:
        logger.error(
            f"[persistence_service] History save FAILED for user_id={user_id} activity_id={activity_id}: {e}"
        )

    # ── Step 3: Analytics upsert ──────────────────────────────────────────────
    try:
        weekly_total, monthly_total, score = _calculate_carbon_totals(db, user_id)
        analytics_repo = AnalyticsRepository(db)
        analytics_repo.create_or_update(
            user_id=user_id,
            weekly_total=weekly_total,
            monthly_total=monthly_total,
            sustainability_score=score,
        )
        logger.info(
            f"[persistence_service] Analytics updated: user_id={user_id} "
            f"weekly={weekly_total:.4f} monthly={monthly_total:.4f} score={score:.1f}"
        )
    except Exception as e:
        logger.error(
            f"[persistence_service] Analytics upsert FAILED for user_id={user_id}: {e}"
        )
