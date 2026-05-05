"""
Journal endpoints — all authenticated.

Routes:
    POST  /journal/entry              Create entry + attach BERT sentiment
    GET   /journal/history            Paginated journal list
    GET   /journal/entry/{id}         Single entry detail
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user_id
from schemas.journal import JournalCreate, JournalHistoryOut, JournalOut
from services import journal_service

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post(
    "/entry",
    response_model=JournalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create journal entry",
    description=(
        "Save a journal entry. The response includes a BERT-calculated "
        "sentiment_label and sentiment_score attached synchronously. "
        "When the async ML worker is live, these will be populated via background task."
    ),
)
async def create_entry(
    payload: JournalCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> JournalOut:
    entry = await journal_service.create_entry(db, user_id, payload)
    return JournalOut.model_validate(entry)


@router.get(
    "/history",
    response_model=JournalHistoryOut,
    summary="List journal entries",
    description="Returns paginated journal entries ordered newest-first.",
)
async def get_history(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=50, description="Records per page"),
) -> JournalHistoryOut:
    entries, total = await journal_service.get_history(db, user_id, page, page_size)
    return JournalHistoryOut(
        entries=[JournalOut.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/entry/{journal_id}",
    response_model=JournalOut,
    summary="Get single journal entry",
    description="Fetch a specific journal entry. Returns 403 if the entry belongs to another user.",
)
async def get_entry(
    journal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> JournalOut:
    entry = await journal_service.get_entry(db, user_id, journal_id)
    return JournalOut.model_validate(entry)