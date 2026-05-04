"""
services/journal_service.py
────────────────────────────
Journal business logic.

BERT sentiment analysis is intentionally stubbed here.
When the ml/ module is ready, replace _analyse_sentiment()
with the real call — the rest of the service stays unchanged.

Public interface:
    create_entry(db, user_id, payload)              → Journal
    get_history(db, user_id, page, page_size)       → (list[Journal], total)
    get_entry(db, user_id, journal_id)              → Journal
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ForbiddenError, NotFoundError
from models.journal import Journal
from schemas.journal import JournalCreate

import logging
from core.config import settings
from models.risk_log import RiskLog, RiskLevel

logger = logging.getLogger(__name__)

_RISK_PTS_DEEP_HOPELESSNESS = 20

#  Sentiment stub 

async def _analyse_sentiment(text: str) -> tuple[str | None, float | None]:
    """
    Stub: returns a neutral sentiment until the BERT service is wired in.

    Replace this with:
        from ml.bert_service import classify_sentiment
        return await classify_sentiment(text)

    Returns:
        (label, score)  e.g. ("neutral", 0.61)
    """
    try:
        from ml import bert_classifier
        result = await bert_classifier.classify_text(text)
        return result.label, result.score
    except Exception as e:
        logger.warning(f"BERT sentiment analysis failed for journal: {e}")
        return None, None


async def _check_and_log_hopelessness(
    db: AsyncSession,
    user_id: UUID,
    label: str | None,
    score: float | None,
) -> None:
    """
    PRD §7.1 — if BERT detects deep hopelessness in a journal entry,
    log 20 risk points. Called after sentiment analysis.
    """
    if label not in ("hopelessness", "suicidal") or score is None:
        return
    # Use the same threshold as bert_classifier.py
    if score < 0.70:
        return

    total_points = _RISK_PTS_DEEP_HOPELESSNESS
    risk_level = (
        RiskLevel.SEVERE   if total_points >= settings.RISK_SEVERE_THRESHOLD   else
        RiskLevel.MODERATE if total_points >= settings.RISK_MODERATE_THRESHOLD else
        RiskLevel.MILD
    )
    db.add(RiskLog(
        user_id=user_id,
        risk_level=risk_level,
        trigger_source="Journal (BERT Deep Hopelessness)",
        total_points=total_points,
        action_taken="Flagged for weekly fusion model. Moderate/Severe action if threshold met.",
    ))
    await db.flush()


# service functions 

async def create_entry(
    db: AsyncSession,
    user_id: UUID,
    payload: JournalCreate,
) -> Journal:
    """
    Save a journal entry and synchronously attach a BERT sentiment score.

    In production this will be fire-and-forget async once the ML worker
    queue is in place. For now the stub runs inline within the request.
    """
    label, score = await _analyse_sentiment(payload.content)

    entry = Journal(
        user_id=user_id,
        content=payload.content,
        sentiment_label=label,
        sentiment_score=score,
    )
    db.add(entry)
    await db.flush()
    await _check_and_log_hopelessness(db, user_id, label, score)

    return entry


async def get_history(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Journal], int]:
    """
    Return paginated journal entries for the user, newest first.

    Returns:
        (entries, total_count)
    """
    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count()).select_from(Journal).where(Journal.user_id == user_id)
    )
    total: int = total_result.scalar_one()

    data_result = await db.execute(
        select(Journal)
        .where(Journal.user_id == user_id)
        .order_by(Journal.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    entries = list(data_result.scalars().all())

    return entries, total


async def get_entry(
    db: AsyncSession,
    user_id: UUID,
    journal_id: UUID,
) -> Journal:
    """
    Fetch a single journal entry, enforcing ownership.

    Raises:
        NotFoundError:  if the entry does not exist.
        ForbiddenError: if the entry belongs to a different user.
    """
    result = await db.execute(
        select(Journal).where(Journal.id == journal_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise NotFoundError("Journal entry not found.")
    if entry.user_id != user_id:
        raise ForbiddenError("You do not have access to this journal entry.")

    return entry