from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    phone_number = Column(String(50), nullable=True)
    date_of_birth = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    college = Column(String(200), nullable=True)
    department = Column(String(200), nullable=True)
    bio = Column(String(1000), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

__all__ = ["UserProfile"]
