"""
user.py — CarbonTracker User Model (Phase I.1)
================================================
Re-exports the canonical User model from models.py.
Provides the `from app.models.user import User` import path required by Phase I.1.
"""
from app.models.models import User

__all__ = ["User"]
