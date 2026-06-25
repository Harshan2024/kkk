from typing import Optional
from sqlalchemy.orm import Session
from app.models.user_profile import UserProfile
from app.utils.logger import log_structured

class ProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        log_structured("INFO", "profile_repository", f"Querying user profile for user_id={user_id}")
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            log_structured("INFO", "profile_repository", f"Found profile record in DB for user_id={user_id}")
        else:
            log_structured("INFO", "profile_repository", f"No profile record found in DB for user_id={user_id}")
        return profile

    def create_profile(self, user_id: int, **kwargs) -> UserProfile:
        log_structured("INFO", "profile_repository", f"Creating new user profile for user_id={user_id} with kwargs={kwargs}")
        profile = UserProfile(user_id=user_id, **kwargs)
        try:
            self.db.add(profile)
            log_structured("INFO", "profile_repository", "SQL database add profile operation staged")
            self.db.commit()
            log_structured("INFO", "profile_repository", "SQL database commit profile transaction successful")
            self.db.refresh(profile)
            log_structured("INFO", "profile_repository", "SQL database refresh profile details loaded")
            return profile
        except Exception as e:
            log_structured("ERROR", "profile_repository", f"SQL database commit failed for create_profile: {e}", exception=e)
            self.db.rollback()
            log_structured("INFO", "profile_repository", "SQL database transaction rolled back successfully")
            raise e

    def update_profile(self, user_id: int, data: dict) -> Optional[UserProfile]:
        log_structured("INFO", "profile_repository", f"Updating user profile for user_id={user_id} with data={data}")
        profile = self.get_by_user_id(user_id)
        if not profile:
            log_structured("INFO", "profile_repository", f"Profile does not exist, creating profile first for user_id={user_id}")
            profile = self.create_profile(user_id)
        
        for key, value in data.items():
            if hasattr(profile, key) and key != "user_id":
                old_val = getattr(profile, key)
                setattr(profile, key, value)
                log_structured("INFO", "profile_repository", f"Staged change user_id={user_id}: {key} = '{old_val}' -> '{value}'")
        
        try:
            self.db.commit()
            log_structured("INFO", "profile_repository", f"SQL database commit profile update transaction successful for user_id={user_id}")
            self.db.refresh(profile)
            log_structured("INFO", "profile_repository", f"SQL database refresh profile details loaded for user_id={user_id}")
            return profile
        except Exception as e:
            log_structured("ERROR", "profile_repository", f"SQL database commit failed for update_profile: {e}", exception=e)
            self.db.rollback()
            log_structured("INFO", "profile_repository", f"SQL database transaction rolled back for user_id={user_id}")
            raise e

    def update_avatar(self, user_id: int, avatar_url: str) -> Optional[UserProfile]:
        log_structured("INFO", "profile_repository", f"Updating avatar url for user_id={user_id} to '{avatar_url}'")
        profile = self.get_by_user_id(user_id)
        if not profile:
            log_structured("INFO", "profile_repository", f"Profile does not exist, creating profile first for user_id={user_id}")
            profile = self.create_profile(user_id)
        
        old_avatar = profile.profile_picture
        profile.profile_picture = avatar_url
        log_structured("INFO", "profile_repository", f"Staged change user_id={user_id}: profile_picture = '{old_avatar}' -> '{avatar_url}'")
        try:
            self.db.commit()
            log_structured("INFO", "profile_repository", f"SQL database commit avatar transaction successful for user_id={user_id}")
            self.db.refresh(profile)
            log_structured("INFO", "profile_repository", f"SQL database refresh profile details loaded for user_id={user_id}")
            return profile
        except Exception as e:
            log_structured("ERROR", "profile_repository", f"SQL database commit failed for update_avatar: {e}", exception=e)
            self.db.rollback()
            log_structured("INFO", "profile_repository", f"SQL database transaction rolled back for user_id={user_id}")
            raise e
