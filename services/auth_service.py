"""
All authentication business logic lives here.
"""

import random
import string
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.redis import blocklist_token, get_redis
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from core.email import email_service
from core.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from models.user import User
from models.user_settings import UserSettings
from models.otp_code import OtpCode
from models.ai_analysis_result import AiAnalysisResult
from schemas.user import UserCreate


#  Internal helpers 

def _generate_otp(length: int = 6) -> str:
    """Return a zero-padded numeric OTP string."""
    return "".join(random.choices(string.digits, k=length))


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _get_valid_otp(db: AsyncSession, user_id: UUID, code: str) -> OtpCode | None:
    """Return an OTP row only if it exists, is unused, and has not expired."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(OtpCode).where(
            OtpCode.user_id == user_id,
            OtpCode.code == code,
            OtpCode.is_used == False,       # noqa: E712
            OtpCode.expires_at > now,
        )
    )
    return result.scalar_one_or_none()


async def _store_otp_in_redis(user_id: UUID, code: str) -> None:
    """
    Mirror the OTP in Redis for fast lookup during verification.
    Key: otp:{user_id}  TTL: OTP_EXPIRE_MINUTES * 60 seconds
    """
    redis = get_redis()
    ttl = settings.OTP_EXPIRE_MINUTES * 60
    await redis.setex(f"otp:{user_id}", ttl, code)


async def _invalidate_otp_in_redis(user_id: UUID) -> None:
    redis = get_redis()
    await redis.delete(f"otp:{user_id}")


# service functions 

async def register_user(db: AsyncSession, payload: UserCreate) -> User:
    """
    Create a new unverified user and persist an OTP for email verification.
    Raises:
        ConflictError: if the email is already registered.
    """
    # Duplicate check
    existing = await _get_user_by_email(db, payload.email)
    if existing:
        raise ConflictError("An account with this email already exists.")

    # Create user + default settings in a single transaction
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()  # populates user.id without committing yet

    default_settings = UserSettings(user_id=user.id)
    db.add(default_settings)

    # Generate and persist OTP
    code = _generate_otp()
    otp = OtpCode(user_id=user.id, code=code)
    db.add(otp)
    

    await db.flush()
    await _store_otp_in_redis(user.id, code)

    try:
        await email_service.send_otp_email(user.email, code)
    except Exception as e:
        print(f"Failed to send email: {e}")

    return user


async def verify_otp(db: AsyncSession, email: str, code: str) -> User:
    """
    Mark the user as verified after a valid OTP is submitted.

    Raises:
        NotFoundError: if the email doesn't exist.
        ValidationError: if the OTP is wrong, expired, or already used.
    """
    user = await _get_user_by_email(db, email)
    if not user:
        raise NotFoundError("No account found with this email.")

    otp_row = await _get_valid_otp(db, user.id, code)
    if not otp_row:
        raise ValidationError("Invalid or expired OTP. Please request a new one.")

    # Mark OTP consumed and activate the account
    otp_row.is_used = True
    user.is_verified = True

    await _invalidate_otp_in_redis(user.id)

    return user


async def resend_otp(db: AsyncSession, email: str) -> None:
    """
    Invalidate all existing OTPs for the user and issue a fresh one.

    Raises:
        NotFoundError: if the email doesn't exist.
        ValidationError: if the account is already verified.
    """
    user = await _get_user_by_email(db, email)
    if not user:
        raise NotFoundError("No account found with this email.")

    # if user.is_verified:
    #     raise ValidationError("This account is already verified.")

    # Invalidate all previous OTPs for this user
    await db.execute(delete(OtpCode).where(OtpCode.user_id == user.id))
    await _invalidate_otp_in_redis(user.id)

    # Issue fresh OTP
    code = _generate_otp()
    db.add(OtpCode(user_id=user.id, code=code))
    await db.flush()
    await _store_otp_in_redis(user.id, code)

    await email_service.send_otp_email(user.email, code)


async def login_user(
    db: AsyncSession, email: str, password: str
) -> tuple[str, str]:
    """
    Authenticate credentials and return a fresh token pair.

    Returns:
        (access_token, refresh_token)

    Raises:
        UnauthorizedError: on wrong credentials or unverified account.
    """
    user = await _get_user_by_email(db, email)

    # Deliberate: same error for wrong email OR wrong password 
    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password.")

    if not user.is_verified:
        raise UnauthorizedError("Please verify your email before logging in.")

    return create_access_token(user.id), create_refresh_token(user.id)


async def refresh_tokens(refresh_token: str) -> tuple[str, str]:
    """
    Validate a refresh token and return a new token pair.
    The old refresh token is blocklisted immediately.

    Returns:
        (new_access_token, new_refresh_token)

    Raises:
        UnauthorizedError: if the token is invalid, expired, or already used.
    """
    try:
        payload = await decode_token(refresh_token)
    except ValueError as exc:
        raise UnauthorizedError(str(exc))

    if payload.type != "refresh":
        raise UnauthorizedError("Only refresh tokens can be used for token rotation.")

    # Blocklist the consumed refresh token (token rotation — prevents reuse)
    remaining_ttl = int(
        (payload.exp - datetime.now(timezone.utc)).total_seconds()
    )
    if remaining_ttl > 0:
        await blocklist_token(payload.jti, remaining_ttl)

    user_id = UUID(payload.sub)
    return create_access_token(user_id), create_refresh_token(user_id)


async def logout_user(access_token: str) -> None:
    """
    Blocklist the current access token so it cannot be reused.

    Raises:
        UnauthorizedError: if the token is already invalid.
    """
    try:
        payload = await decode_token(access_token)
    except ValueError as exc:
        raise UnauthorizedError(str(exc))

    remaining_ttl = int(
        (payload.exp - datetime.now(timezone.utc)).total_seconds()
    )
    if remaining_ttl > 0:
        await blocklist_token(payload.jti, remaining_ttl)


async def change_password(
    db: AsyncSession, user_id: UUID, current_password: str, new_password: str
) -> None:
    """
    Verify the current password then replace it with a new bcrypt hash.

    Raises:
        NotFoundError: if the user doesn't exist.
        UnauthorizedError: if current_password is wrong.
    """
    user = await _get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found.")

    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect.")

    user.password_hash = hash_password(new_password)


async def delete_account(db: AsyncSession, user_id: UUID) -> None:
    """
    Permanently delete the user row and cascade-wipe all related data.
    AiAnalysisResult rows (raw ML outputs) are explicitly cleared first
    to satisfy the PRD privacy requirement.

    Raises:
        NotFoundError: if the user doesn't exist.
    """
    user = await _get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found.")

    # Explicit wipe of AI analysis data first.
    # Walk: ai_analysis_results → chat_messages → chat_sessions → user
    from models.chat_message import ChatMessage
    from models.chat_session import ChatSession

    ai_message_ids_subq = (
        select(ChatMessage.id)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == user_id)
        .scalar_subquery()
    )
    await db.execute(
        delete(AiAnalysisResult).where(
            AiAnalysisResult.message_id.in_(ai_message_ids_subq)
        )
    )

    # CASCADE DELETE on the users table handles all remaining related rows.
    await db.delete(user)