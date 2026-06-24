"""
activity_entity.py — CarbonTracker ActivityEntity Model (Phase I.1)
====================================================================
Defines the `activity_entities` table.

Each row represents one extracted entity from a natural-language activity log.
For example, "I travelled 25 km by train and 10 km by car" produces two
ActivityEntity rows: one for Train and one for Car.

Fields:
  id               — Primary key
  activity_id      — FK → activities.id
  entity_name      — e.g. "Train", "Car", "Beef"
  entity_category  — e.g. "transport", "food"
  quantity         — Numeric amount (e.g. 25.0)
  unit             — Unit of measure (e.g. "km", "kg")
  factor           — Emission factor used (e.g. 0.02 kgCO2e/km)
  carbon_emission  — Final emission value in kgCO2e (e.g. 0.50)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class ActivityEntity(Base):
    """
    Stores individual entities extracted from a multi-entity activity log.
    Preserves Phase D multi-entity results for persistence and analytics.
    """
    __tablename__ = "activity_entities"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(
        Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_name = Column(String(255), nullable=False, index=True)
    entity_category = Column(String(100), nullable=True, index=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    factor = Column(Float, nullable=True)
    carbon_emission = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    activity = relationship("Activity", back_populates="entities")


__all__ = ["ActivityEntity"]
