from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Payload for POST /auth/login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Returned on successful login or token refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OtpVerifyRequest(BaseModel):
    """Payload for POST /auth/verify-otp"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ChangePasswordRequest(BaseModel):
    """Payload for PUT /user/change-password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ResendOtpRequest(BaseModel):
    email: EmailStr