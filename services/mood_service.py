"""
Mood log business logic.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from models.mood_log import MoodLog
from schemas.mood_log import MoodLogCreate


#  service functions 

async def log_mood(
    db: AsyncSession,
    user_id: UUID,
    payload: MoodLogCreate,
) -> MoodLog:
    """
    Persist a new mood log entry for the authenticated user.

    The mood_score is validated 1-10 by Pydantic before reaching here,
    and enforced again at the DB level via CheckConstraint.
    """
    entry = MoodLog(
        user_id=user_id,
        mood_score=payload.mood_score,
        mood_label=payload.mood_label,
    )
    db.add(entry)
    await db.flush()  # populate entry.id before returning
    return entry


async def get_mood_history(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 30,
) -> tuple[list[MoodLog], int]:
    """
    Return a paginated list of mood logs ordered newest-first,
    plus the total count (for the chart and pagination metadata).

    Returns:
        (logs, total_count)
    """
    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count()).select_from(MoodLog).where(MoodLog.user_id == user_id)
    )
    total: int = total_result.scalar_one()

    data_result = await db.execute(
        select(MoodLog)
        .where(MoodLog.user_id == user_id)
        .order_by(MoodLog.logged_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = list(data_result.scalars().all())

    return logs, total