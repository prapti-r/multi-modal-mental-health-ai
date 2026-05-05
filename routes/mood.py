"""
Mood tracking endpoints — all authenticated.

Routes:
    POST  /mood/log        Submit a daily mood score
    GET   /mood/history    Paginated mood history (chart-ready)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user_id
from schemas.mood_log import MoodHistoryOut, MoodLogCreate, MoodLogOut
from services import mood_service

router = APIRouter(prefix="/mood", tags=["Mood Tracking"])


@router.post(
    "/log",
    response_model=MoodLogOut,
    status_code=status.HTTP_201_CREATED,
    summary="Log daily mood",
    description="Submit a mood score (1–10) and a label. One entry per day is typical.",
)
async def log_mood(
    payload: MoodLogCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MoodLogOut:
    entry = await mood_service.log_mood(db, user_id, payload)
    return MoodLogOut.model_validate(entry)


@router.get(
    "/history",
    response_model=MoodHistoryOut,
    summary="Get mood history",
    description=(
        "Returns paginated mood logs ordered newest-first. "
        "Default page_size=30 covers one month of daily logs. "
        "The `data_points` array maps directly to a React Native line chart."
    ),
)
async def get_mood_history(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=30, ge=1, le=90, description="Records per page"),
) -> MoodHistoryOut:
    logs, total = await mood_service.get_mood_history(db, user_id, page, page_size)
    return MoodHistoryOut(
        data_points=[MoodLogOut.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )