from sqlalchemy.orm import Session
from app.models.models import User
from app.repositories.profile_repository import ProfileRepository
from datetime import datetime

class ProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProfileRepository(db)

    def get_or_create_profile(self, user: User) -> dict:
        profile = self.repo.get_by_user_id(user.id)
        if not profile:
            profile = self.repo.create_profile(user_id=user.id)
        
        achievements_count = 0
        joined_date = user.created_at.isoformat() + "Z" if user.created_at else datetime.utcnow().isoformat() + "Z"
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": joined_date,
            "joined_date": joined_date,  # support both names for safety
            "xp": user.xp,
            "level": user.level,
            "achievements_count": achievements_count,
            "carbon_score": 0.0,
            "full_name": profile.full_name or "",
            "phone_number": profile.phone_number or "",
            "date_of_birth": profile.date_of_birth or "",
            "gender": profile.gender or "",
            "location": profile.location or "",
            "country": profile.country or "",
            "college": profile.college or "",
            "department": profile.department or "",
            "bio": profile.bio or "",
            "profile_picture": profile.profile_picture or "",
            "auth_provider": "local"
        }

    def update_profile(self, user: User, data: dict) -> dict:
        self.repo.update_profile(user.id, data)
        return self.get_or_create_profile(user)

    def update_avatar(self, user: User, avatar_url: str) -> dict:
        self.repo.update_avatar(user.id, avatar_url)
        return self.get_or_create_profile(user)
