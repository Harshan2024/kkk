"""
analytics.py — CarbonTracker Analytics Snapshot Model (Phase I.1)
==================================================================
Defines the `analytics` table.

Stores periodic analytics snapshots per user. The Analytics Engine is NOT
yet wired to this table — that happens in a later phase. This model
provides the persistence layer for snapshots when that connection is made.

Fields:
  id                   — Primary key
  user_id              — FK → users.id
  weekly_total         — Total kgCO2e for the current week
  monthly_total        — Total kgCO2e for the current month
  sustainability_score — Computed sustainability score (0–100)
  last_updated         — Timestamp of last snapshot update
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Analytics(Base):
    """
    Analytics snapshot — stores periodic sustainability metrics per user.
    The Analytics Engine connection is deferred to a later phase.
    """
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weekly_total = Column(Float, nullable=True, default=0.0)
    monthly_total = Column(Float, nullable=True, default=0.0)
    sustainability_score = Column(Float, nullable=True, default=100.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")


__all__ = ["Analytics"]
