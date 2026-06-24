from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import User
from datetime import datetime

class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        if not email:
            return None
        return self.db.query(User).filter(func.lower(User.email) == func.lower(email)).first()

    def get_by_username(self, username: str) -> Optional[User]:
        if not username:
            return None
        return self.db.query(User).filter(func.lower(User.username) == func.lower(username)).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, username: str, email: str, hashed_password: str) -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
            role="user",
            xp=0,
            level=1,
            redeemed_rewards=[]
        )
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise e

    def update_user_login(self, user_id: int) -> None:
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()

    def update_user_profile(self, user_id: int, username: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        user.updated_at = datetime.utcnow()
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise e

    def update_user_password(self, user_id: int, hashed_password: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        user.hashed_password = hashed_password
        user.updated_at = datetime.utcnow()
        try:
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
