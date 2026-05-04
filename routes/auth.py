"""
routes/auth.py
──────────────
Authentication endpoints — all under /api/v1/auth/* and /api/v1/user/*

Routes implemented:
    POST   /auth/register          Register + trigger OTP email
    POST   /auth/verify-otp        Verify OTP → activate account
    POST   /auth/resend-otp        Request a fresh OTP
    POST   /auth/login             Authenticate → token pair
    POST   /auth/refresh           Rotate token pair using refresh token
    POST   /auth/logout            Blocklist current access token
    PUT    /user/change-password   Change password (authenticated)
    DELETE /user/account           Delete account + wipe AI data
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user_id
from schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    OtpVerifyRequest,
    TokenResponse,
    ResendOtpRequest,
)
from schemas.user import UserCreate, UserOut
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_router = APIRouter(prefix="/user", tags=["User Account"])

_bearer = HTTPBearer(auto_error=True)


# Registration 

@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates an unverified account and dispatches a 6-digit OTP "
        "to the provided email. The account cannot be used until verified."
    ),
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await auth_service.register_user(db, payload)
    return UserOut.model_validate(user)


# OTP verification

@router.post(
    "/verify-otp",
    response_model=UserOut,
    summary="Verify email with OTP",
    description="Accepts the 6-digit OTP sent during registration and activates the account.",
)
async def verify_otp(
    payload: OtpVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await auth_service.verify_otp(db, payload.email, payload.code)
    return UserOut.model_validate(user)


@router.post(
    "/resend-otp",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Resend OTP",
    description="Invalidates any existing OTPs and issues a fresh one to the registered email.",
)
async def resend_otp(
    payload: ResendOtpRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    # We only need the email here — use ResendOtpRequest.email
    await auth_service.resend_otp(db, payload.email)


# Login / token management 

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive token pair",
    description=(
        "Authenticates credentials and returns an access token (short-lived) "
        "and a refresh token (long-lived). Store both securely on the client."
    ),
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    access_token, refresh_token = await auth_service.login_user(
        db, payload.email, payload.password
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate token pair",
    description=(
        "Accepts a valid refresh token and returns a new access + refresh token pair. "
        "The submitted refresh token is immediately blocklisted (token rotation)."
    ),
)
async def refresh(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TokenResponse:
    access_token, refresh_token = await auth_service.refresh_tokens(
        credentials.credentials
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout — invalidate access token",
    description=(
        "Adds the current access token's JTI to the Redis blocklist "
        "so it cannot be reused, even before it naturally expires."
    ),
)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> None:
    await auth_service.logout_user(credentials.credentials)


# Authenticated user account operations 

@user_router.put(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Verifies the current password then replaces it with a new bcrypt hash.",
)
async def change_password(
    payload: ChangePasswordRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await auth_service.change_password(
        db, user_id, payload.current_password, payload.new_password
    )


@user_router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account",
    description=(
        "Permanently deletes the user's account and all associated data. "
        "AI analysis results are explicitly wiped first per the privacy policy."
    ),
)
async def delete_account(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await auth_service.delete_account(db, user_id)