"""
user_repository.py — CarbonTracker User Repository (Phase I.1)
===============================================================
CRUD operations for the User model.

All methods accept a SQLAlchemy Session and return model instances or None.
No business logic — pure data access layer.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import User


class UserRepository:
    """
    Data access layer for the `users` table.

    Usage:
        repo = UserRepository(db)
        user = repo.create(username="alice")
    """

    def __init__(self, db: Session):
        self.db = db

    # ─── CREATE ──────────────────────────────────────────────────────────────

    def create(self, username: str, xp: int = 0, level: int = 1) -> User:
        """
        Create a new User and persist to the database.

        Args:
            username: Unique username string.
            xp:       Starting XP (default 0).
            level:    Starting level (default 1).

        Returns:
            The newly created User instance (with id populated).

        Raises:
            sqlalchemy.exc.IntegrityError: If username already exists.
        """
        user = User(username=username, xp=xp, level=level)
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise e

    # ─── READ ────────────────────────────────────────────────────────────────

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Return User by primary key, or None if not found."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Return User by username (case-sensitive), or None if not found."""
        return self.db.query(User).filter(User.username == username).first()

    def get_or_create(self, username: str) -> tuple[User, bool]:
        """
        Return existing User or create a new one.

        Returns:
            (user, created) where created=True if a new row was inserted.
        """
        user = self.get_by_username(username)
        if user:
            return user, False
        user = self.create(username=username)
        return user, True

    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Return a paginated list of all users."""
        return self.db.query(User).offset(skip).limit(limit).all()

    # ─── UPDATE ──────────────────────────────────────────────────────────────

    def update(
        self,
        user_id: int,
        username: Optional[str] = None,
        xp: Optional[int] = None,
        level: Optional[int] = None,
    ) -> Optional[User]:
        """
        Update User fields. Only non-None arguments are applied.

        Returns:
            Updated User instance, or None if user_id not found.
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        if username is not None:
            user.username = username
        if xp is not None:
            user.xp = xp
        if level is not None:
            user.level = level
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise e

    def add_xp(self, user_id: int, points: int) -> Optional[User]:
        """Increment a user's XP by `points`. Returns updated User or None."""
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.xp = (user.xp or 0) + points
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise e

    # ─── DELETE ──────────────────────────────────────────────────────────────

    def delete(self, user_id: int) -> bool:
        """
        Delete a User by primary key. Cascade deletes all related records.

        Returns:
            True if a row was deleted, False if user_id not found.
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
