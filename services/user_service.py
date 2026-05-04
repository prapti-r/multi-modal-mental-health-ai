"""
services/user_service.py
────────────────────────
Profile and settings business logic.

Public interface:
    get_profile(db, user_id)                    → User
    update_profile(db, user_id, payload)        → User
    get_settings(db, user_id)                   → UserSettings
    update_settings(db, user_id, payload)       → UserSettings
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from models.user import User
from models.user_settings import UserSettings
from schemas.user import UserProfileUpdate
from schemas.user_settings import UserSettingsUpdate


#  Internal helpers 

async def _require_user(db: AsyncSession, user_id: UUID) -> User:
    """Fetch a user by ID or raise NotFoundError."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found.")
    return user


async def _require_settings(db: AsyncSession, user_id: UUID) -> UserSettings:
    """Fetch user settings or raise NotFoundError."""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        raise NotFoundError("Settings not found for this user.")
    return settings_row


# service functions 

async def get_profile(db: AsyncSession, user_id: UUID) -> User:
    return await _require_user(db, user_id)


async def update_profile(
    db: AsyncSession, user_id: UUID, payload: UserProfileUpdate
) -> User:
    """
    Apply partial profile updates — only fields explicitly provided are changed.

    Raises:
        NotFoundError: if the user doesn't exist.
    """
    user = await _require_user(db, user_id)

    # model_dump(exclude_unset=True) ensures PATCH semantics:
    # only fields the client sent are written, others are left untouched.
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    return user


async def get_settings(db: AsyncSession, user_id: UUID) -> UserSettings:
    return await _require_settings(db, user_id)


async def update_settings(
    db: AsyncSession, user_id: UUID, payload: UserSettingsUpdate
) -> UserSettings:
    """
    Apply partial settings updates.

    Raises:
        NotFoundError: if settings row doesn't exist for the user.
    """
    settings_row = await _require_settings(db, user_id)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(settings_row, field, value)

    return settings_row