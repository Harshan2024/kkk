from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    scores = relationship("SustainabilityScore", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("AIInsight", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    corrections = relationship("UserCorrection", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    icon = Column(String, nullable=True)


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True, nullable=False)
    item_key = Column(String, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    factor = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    source = Column(String, nullable=True)
    description = Column(String, nullable=True)
    region = Column(String, default="Global", index=True)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    year = Column(Integer, default=2024)
    confidence = Column(Float, default=0.9)


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    input_text = Column(String, nullable=False)
    category = Column(String, index=True, nullable=False)
    item = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    calculated_value = Column(Float, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    region = Column(String, default="Global", index=True)
    logged_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="activities")


class SustainabilityScore(Base):
    __tablename__ = "sustainability_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_emissions = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scores")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    badge_type = Column(String, nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="achievements")


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(String, nullable=False)
    category = Column(String, nullable=True)
    impact_estimate = Column(String, nullable=True)
    impact_level = Column(String, nullable=True, default="MEDIUM") # HIGH, MEDIUM, LOW
    impact_value = Column(Float, nullable=True, default=0.0) # Numerical saving value for priority sorting
    feasibility = Column(String, nullable=True, default="HIGH") # HIGH, MEDIUM, LOW
    difficulty = Column(String, nullable=True, default="EASY") # EASY, MEDIUM, HARD
    confidence_score = Column(Float, nullable=True, default=0.90)
    sustainability_gain = Column(Float, nullable=True, default=5.0)
    behavioral_compatibility = Column(Float, nullable=True, default=5.0)
    why_explanation = Column(String, nullable=True)
    how_calculation = Column(String, nullable=True)
    weighted_priority_score = Column(Float, nullable=True, default=0.0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="insights")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    semantic_summary = Column(String, nullable=True)
    embedding_id = Column(String, nullable=True)
    context_tags = Column(JSON, nullable=True)

    user = relationship("User", back_populates="chat_messages")


class UserCorrection(Base):
    __tablename__ = "user_corrections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_text = Column(String, nullable=False)
    corrected_text = Column(String, nullable=False)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="corrections")
