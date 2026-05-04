"""
schemas/journal.py
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JournalCreate(BaseModel):
    """Payload for POST /journal/entry"""
    content: str = Field(..., min_length=1)


class JournalOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    # Populated after async BERT processing; None until analysis completes
    sentiment_label: str | None
    sentiment_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JournalHistoryOut(BaseModel):
    """Paginated response for GET /journal/history"""
    entries: list[JournalOut]
    total: int
    page: int
    page_size: int