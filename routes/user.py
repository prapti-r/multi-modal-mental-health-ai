"""
User profile and settings endpoints — all authenticated.

Routes implemented:
    GET    /user/profile    Retrieve current user's profile
    PATCH  /user/profile    Partial-update profile (name, avatar URL)
    GET    /user/settings   Retrieve notification / theme preferences
    PUT    /user/settings   Replace settings fields
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user_id
from schemas.user import UserOut, UserProfileUpdate
from schemas.user_settings import UserSettingsOut, UserSettingsUpdate
from services import user_service

router = APIRouter(prefix="/user", tags=["User Profile"])


# Profile 

@router.get(
    "/profile",
    response_model=UserOut,
    summary="Get current user profile",
)
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await user_service.get_profile(db, user_id)
    return UserOut.model_validate(user)


@router.patch(
    "/profile",
    response_model=UserOut,
    summary="Update profile",
    description="Partial update — only provided fields are changed.",
)
async def update_profile(
    payload: UserProfileUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await user_service.update_profile(db, user_id, payload)
    return UserOut.model_validate(user)


# Settings

@router.get(
    "/settings",
    response_model=UserSettingsOut,
    summary="Get user preferences",
)
async def get_settings(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserSettingsOut:
    user_settings = await user_service.get_settings(db, user_id)
    return UserSettingsOut.model_validate(user_settings)


@router.put(
    "/settings",
    response_model=UserSettingsOut,
    summary="Update user preferences",
    description="Updates theme, notification time, or chatbot tone. All fields optional.",
)
async def update_settings(
    payload: UserSettingsUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserSettingsOut:
    user_settings = await user_service.update_settings(db, user_id, payload)
    return UserSettingsOut.model_validate(user_settings)