from pydantic import BaseModel, Field
from typing import Optional, List

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)

class UserLoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ProfileResponse(BaseModel):
    username: str
    email: Optional[str] = None
    xp: int
    level: int
    achievements: List[str] = []
    sustainability_score: float
    joined_date: str

class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
