from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_type = Column(String(100), nullable=False) # emission_reduction, activity, streak, sustainability_score
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    status = Column(String(50), default="active") # active, completed, failed
    progress_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    target_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    user = relationship("User")

__all__ = ["Goal"]
