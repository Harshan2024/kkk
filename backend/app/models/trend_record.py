from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class TrendRecord(Base):
    __tablename__ = "trend_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period_days = Column(Integer, nullable=False) # 30, 60, 90
    trend_pct = Column(Float, nullable=False)
    best_improvement_period = Column(String(100), nullable=True)
    worst_emission_period = Column(String(100), nullable=True)
    most_improved_category = Column(String(100), nullable=True)
    most_problematic_category = Column(String(100), nullable=True)
    consistency_evolution = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

__all__ = ["TrendRecord"]
