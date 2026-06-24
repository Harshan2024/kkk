"""
analytics_repository.py — CarbonTracker Analytics Repository (Phase I.1)
=========================================================================
CRUD operations for the Analytics model.

Supports upsert (create_or_update) semantics so the Analytics Engine can
call a single method regardless of whether a snapshot already exists.
No business logic — pure data access layer.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.analytics import Analytics


class AnalyticsRepository:
    """
    Data access layer for the `analytics` table.

    Usage:
        repo = AnalyticsRepository(db)
        snapshot = repo.create_or_update(
            user_id=1,
            weekly_total=4.2,
            monthly_total=18.5,
            sustainability_score=82.0,
        )
    """

    def __init__(self, db: Session):
        self.db = db

    # ─── CREATE / UPSERT ─────────────────────────────────────────────────────

    def create(
        self,
        user_id: int,
        weekly_total: float = 0.0,
        monthly_total: float = 0.0,
        sustainability_score: float = 100.0,
    ) -> Analytics:
        """
        Create a new Analytics snapshot for a user.

        Returns:
            The newly created Analytics instance.
        """
        snapshot = Analytics(
            user_id=user_id,
            weekly_total=weekly_total,
            monthly_total=monthly_total,
            sustainability_score=sustainability_score,
            last_updated=datetime.utcnow(),
        )
        try:
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            return snapshot
        except Exception as e:
            self.db.rollback()
            raise e

    def create_or_update(
        self,
        user_id: int,
        weekly_total: Optional[float] = None,
        monthly_total: Optional[float] = None,
        sustainability_score: Optional[float] = None,
    ) -> Analytics:
        """
        Upsert analytics snapshot for a user.

        If a row for the user already exists, update it in place.
        Otherwise create a new row.

        Returns:
            The updated or newly created Analytics instance.
        """
        snapshot = self.get_by_user(user_id)
        if snapshot:
            if weekly_total is not None:
                snapshot.weekly_total = weekly_total
            if monthly_total is not None:
                snapshot.monthly_total = monthly_total
            if sustainability_score is not None:
                snapshot.sustainability_score = sustainability_score
            snapshot.last_updated = datetime.utcnow()
            try:
                self.db.commit()
                self.db.refresh(snapshot)
                return snapshot
            except Exception as e:
                self.db.rollback()
                raise e
        else:
            return self.create(
                user_id=user_id,
                weekly_total=weekly_total if weekly_total is not None else 0.0,
                monthly_total=monthly_total if monthly_total is not None else 0.0,
                sustainability_score=sustainability_score if sustainability_score is not None else 100.0,
            )

    # ─── READ ────────────────────────────────────────────────────────────────

    def get_by_id(self, analytics_id: int) -> Optional[Analytics]:
        """Return Analytics snapshot by primary key, or None."""
        return self.db.query(Analytics).filter(Analytics.id == analytics_id).first()

    def get_by_user(self, user_id: int) -> Optional[Analytics]:
        """
        Return the most recent Analytics snapshot for a user, or None.
        Returns a single row (most recently updated).
        """
        return (
            self.db.query(Analytics)
            .filter(Analytics.user_id == user_id)
            .order_by(Analytics.last_updated.desc())
            .first()
        )

    def list_by_user(self, user_id: int, limit: int = 30) -> List[Analytics]:
        """Return all Analytics snapshots for a user, newest first."""
        return (
            self.db.query(Analytics)
            .filter(Analytics.user_id == user_id)
            .order_by(Analytics.last_updated.desc())
            .limit(limit)
            .all()
        )

    # ─── DELETE ──────────────────────────────────────────────────────────────

    def delete(self, analytics_id: int) -> bool:
        """
        Delete an Analytics snapshot by primary key.

        Returns:
            True if deleted, False if not found.
        """
        snapshot = self.get_by_id(analytics_id)
        if not snapshot:
            return False
        try:
            self.db.delete(snapshot)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_by_user(self, user_id: int) -> int:
        """Delete all Analytics rows for a user. Returns count deleted."""
        try:
            count = (
                self.db.query(Analytics)
                .filter(Analytics.user_id == user_id)
                .delete(synchronize_session=False)
            )
            self.db.commit()
            return count
        except Exception as e:
            self.db.rollback()
            raise e
