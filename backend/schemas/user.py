from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime, date

# This schema is used when a user registers (Incoming Data)
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)  # Max 72 for bcrypt compatibility
    full_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    preferred_language: Optional[str] = "en"

# This schema is used for the Login request
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# This schema is used for the API Response (Outgoing Data)
# It excludes the password_hash for security
class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    full_name: str
    is_verified: bool
    is_active: bool
    created_at: datetime

    # Modern Pydantic V2 config to allow compatibility with SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)

# Schema for updating a profile
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    profile_picture: Optional[str] = None
    preferred_language: Optional[str] = None