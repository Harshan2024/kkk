"""
coach_repository.py — CarbonTracker Coach Report Repository (Phase I.1)
========================================================================
CRUD operations for the CoachReport model.

All methods accept a SQLAlchemy Session and return model instances or None.
No business logic — pure data access layer.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.coach_report import CoachReport


class CoachRepository:
    """
    Data access layer for the `coach_reports` table.

    Usage:
        repo = CoachRepository(db)
        report = repo.create(
            user_id=1,
            report_type="weekly_summary",
            report_data={"insights": [...], "score": 85},
        )
    """

    def __init__(self, db: Session):
        self.db = db

    # ─── CREATE ──────────────────────────────────────────────────────────────

    def create(
        self,
        user_id: int,
        report_type: str,
        report_data: Optional[dict] = None,
    ) -> CoachReport:
        """
        Persist a new AI Coach report for a user.

        Args:
            user_id:     FK to users.id
            report_type: Type identifier (e.g. "weekly_summary", "action_plan")
            report_data: JSON-serialisable dict with the full coach output

        Returns:
            The newly created CoachReport instance (with id populated).
        """
        report = CoachReport(
            user_id=user_id,
            report_type=report_type,
            report_data=report_data,
        )
        try:
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            return report
        except Exception as e:
            self.db.rollback()
            raise e

    # ─── READ ────────────────────────────────────────────────────────────────

    def get_by_id(self, report_id: int) -> Optional[CoachReport]:
        """Return CoachReport by primary key, or None if not found."""
        return self.db.query(CoachReport).filter(CoachReport.id == report_id).first()

    def get_by_user(
        self,
        user_id: int,
        report_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CoachReport]:
        """
        Return paginated coach reports for a user, newest first.

        Args:
            user_id:     Filter by user.
            report_type: Optional filter by report type.
            skip:        Pagination offset.
            limit:       Max rows to return.
        """
        query = (
            self.db.query(CoachReport)
            .filter(CoachReport.user_id == user_id)
        )
        if report_type:
            query = query.filter(CoachReport.report_type == report_type)
        return query.order_by(CoachReport.created_at.desc()).offset(skip).limit(limit).all()

    def get_latest_by_user(
        self, user_id: int, report_type: Optional[str] = None
    ) -> Optional[CoachReport]:
        """Return the most recently created CoachReport for a user (optionally by type)."""
        query = self.db.query(CoachReport).filter(CoachReport.user_id == user_id)
        if report_type:
            query = query.filter(CoachReport.report_type == report_type)
        return query.order_by(CoachReport.created_at.desc()).first()

    # ─── DELETE ──────────────────────────────────────────────────────────────

    def delete(self, report_id: int) -> bool:
        """
        Delete a CoachReport by primary key.

        Returns:
            True if deleted, False if not found.
        """
        report = self.get_by_id(report_id)
        if not report:
            return False
        try:
            self.db.delete(report)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_by_user(self, user_id: int) -> int:
        """Delete all CoachReports for a user. Returns count deleted."""
        try:
            count = (
                self.db.query(CoachReport)
                .filter(CoachReport.user_id == user_id)
                .delete(synchronize_session=False)
            )
            self.db.commit()
            return count
        except Exception as e:
            self.db.rollback()
            raise e
