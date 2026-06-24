from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class UserSustainabilityProfile(Base):
    __tablename__ = "user_sustainability_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    primary_lifestyle_type = Column(String(100), nullable=True)
    transport_profile = Column(String(100), nullable=True)
    food_profile = Column(String(100), nullable=True)
    energy_profile = Column(String(100), nullable=True)
    waste_profile = Column(String(100), nullable=True)
    overall_maturity = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")

__all__ = ["UserSustainabilityProfile"]
