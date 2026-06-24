"""
history.py — CarbonTracker History Model (Phase I.1)
=====================================================
Defines the `history` table.

Replaces the existing in-memory / transient history storage with a persistent
PostgreSQL-backed log. Each row links a User to an Activity at a point in time.

Fields:
  id           — Primary key
  user_id      — FK → users.id
  activity_id  — FK → activities.id
  created_at   — Timestamp when the history entry was recorded
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class History(Base):
    """
    Persistent history log — replaces temporary in-memory history storage.
    Links User ↔ Activity with a timestamp for audit and retrieval.
    """
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id = Column(
        Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")
    activity = relationship("Activity")


__all__ = ["History"]
