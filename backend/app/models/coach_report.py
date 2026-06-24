"""
coach_report.py — CarbonTracker AI Coach Report Model (Phase I.1)
==================================================================
Defines the `coach_reports` table.

Stores AI Coach outputs (recommendations, summaries, action plans) per user.
The AI Coach Engine is NOT yet wired to this table — that happens in a later
phase. This model provides the persistence layer for when that wiring occurs.

Fields:
  id           — Primary key
  user_id      — FK → users.id
  report_type  — Type of report: e.g. "weekly_summary", "action_plan", "insight"
  report_data  — JSON payload containing the full coach output
  created_at   — Timestamp when the report was generated
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base


class CoachReport(Base):
    """
    Persistent AI Coach report — stores structured coach outputs per user.
    AI Coach Engine connection is deferred to a later phase.
    """
    __tablename__ = "coach_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_type = Column(String(100), nullable=False, index=True)
    report_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")


__all__ = ["CoachReport"]
