import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


#  Register 
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class RegisterResponse(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    message: str = "Account created successfully"

    class Config:
        from_attributes = True


#  Login 
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    full_name: str


#  Refresh 
class RefreshRequest(BaseModel):
    refresh_token: str


#  Password Reset 
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


#  Profile 
class UserProfile(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    preferred_language: str
    is_verified: bool
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True