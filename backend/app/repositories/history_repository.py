"""
history_repository.py — CarbonTracker History Repository (Phase I.1)
=====================================================================
CRUD operations for the History model.

All methods accept a SQLAlchemy Session and return model instances or None.
No business logic — pure data access layer.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.history import History


class HistoryRepository:
    """
    Data access layer for the `history` table.

    Usage:
        repo = HistoryRepository(db)
        entry = repo.create(user_id=1, activity_id=42)
    """

    def __init__(self, db: Session):
        self.db = db

    # ─── CREATE ──────────────────────────────────────────────────────────────

    def create(self, user_id: int, activity_id: int) -> History:
        """
        Create a new History entry linking a User to an Activity.

        Args:
            user_id:     FK to users.id
            activity_id: FK to activities.id

        Returns:
            The newly created History instance (with id populated).
        """
        entry = History(user_id=user_id, activity_id=activity_id)
        try:
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            return entry
        except Exception as e:
            self.db.rollback()
            raise e

    # ─── READ ────────────────────────────────────────────────────────────────

    def get_by_id(self, history_id: int) -> Optional[History]:
        """Return History entry by primary key, or None if not found."""
        return self.db.query(History).filter(History.id == history_id).first()

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[History]:
        """
        Return a paginated history log for a user, most recent first.

        Args:
            user_id: The user whose history to retrieve.
            skip:    Pagination offset.
            limit:   Maximum rows to return.
        """
        return (
            self.db.query(History)
            .filter(History.user_id == user_id)
            .order_by(History.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_activity(self, activity_id: int) -> List[History]:
        """Return all history entries associated with a given activity."""
        return (
            self.db.query(History)
            .filter(History.activity_id == activity_id)
            .all()
        )

    # ─── DELETE ──────────────────────────────────────────────────────────────

    def delete(self, history_id: int) -> bool:
        """
        Delete a History entry by primary key.

        Returns:
            True if deleted, False if not found.
        """
        entry = self.get_by_id(history_id)
        if not entry:
            return False
        try:
            self.db.delete(entry)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_by_user(self, user_id: int) -> int:
        """
        Delete all history entries for a user. Returns count of deleted rows.
        Useful for user data deletion / GDPR compliance.
        """
        try:
            count = (
                self.db.query(History)
                .filter(History.user_id == user_id)
                .delete(synchronize_session=False)
            )
            self.db.commit()
            return count
        except Exception as e:
            self.db.rollback()
            raise e
