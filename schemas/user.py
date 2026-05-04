import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    """Payload for POST /auth/register"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserOut(BaseModel):
    """Safe user representation — never exposes password_hash."""
    id: uuid.UUID
    full_name: str
    email: EmailStr
    profile_image_url: str | None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Payload for PATCH /user/profile"""
    full_name: str | None = Field(None, min_length=2, max_length=100)
    profile_image_url: str | None = None