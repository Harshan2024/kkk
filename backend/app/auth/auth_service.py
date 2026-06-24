import re
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.auth_models import (
    UserRegisterRequest,
    UserLoginRequest,
    ProfileUpdateRequest,
)
from app.auth.auth_repository import AuthRepository
from app.auth.password_service import PasswordService
from app.auth.jwt_service import JWTService
from app.models.models import User

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)

    def register_user(self, req: UserRegisterRequest) -> User:
        # Validate email format
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, req.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        # Validate password strength
        if not PasswordService.validate_password_strength(req.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long, contain at least one uppercase letter, and one number"
            )

        # Check unique constraints
        if self.repo.get_by_email(req.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if self.repo.get_by_username(req.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        hashed = PasswordService.hash_password(req.password)
        return self.repo.create_user(
            username=req.username,
            email=req.email,
            hashed_password=hashed
        )

    def login_user(self, req: UserLoginRequest) -> dict:
        user = self.repo.get_by_email(req.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not PasswordService.verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )

        # Update login timestamp
        self.repo.update_user_login(user.id)

        # Generate tokens
        access_token = JWTService.create_access_token({"sub": user.username})
        refresh_token = JWTService.create_refresh_token({"sub": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def request_reset(self, email: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user:
            # Generic success for security
            return {
                "success": True,
                "message": "Password reset email requested (mock)",
                "token": "mock_invalid_token"
            }

        # Generate a password reset token (expiring in 15 minutes)
        reset_token = JWTService.create_access_token({"sub": user.username, "reset": True}, expires_delta=timedelta(minutes=15))
        return {
            "success": True,
            "message": "Password reset email requested (mock)",
            "token": reset_token
        }

    def confirm_reset(self, token: str, new_password: str) -> bool:
        if not PasswordService.validate_password_strength(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long, contain at least one uppercase letter, and one number"
            )

        payload = JWTService.decode_token(token)
        if not payload or payload.get("reset") is not True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        username = payload.get("sub")
        user = self.repo.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        hashed = PasswordService.hash_password(new_password)
        return self.repo.update_user_password(user.id, hashed)

    def get_profile(self, user: User) -> dict:
        return {
            "username": user.username,
            "email": user.email,
            "xp": user.xp,
            "level": user.level,
            "achievements": [a.name for a in user.achievements],
            "sustainability_score": user.sustainability_score,
            "joined_date": user.created_at.isoformat() + "Z" if user.created_at else ""
        }

    def update_profile(self, user: User, req: ProfileUpdateRequest) -> User:
        if req.username is not None and req.username != user.username:
            if self.repo.get_by_username(req.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        if req.email is not None and req.email != user.email:
            if self.repo.get_by_email(req.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
                
        return self.repo.update_user_profile(
            user_id=user.id,
            username=req.username,
            email=req.email
        )
