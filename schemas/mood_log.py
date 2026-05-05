import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MoodLogCreate(BaseModel):
    """Payload for POST /mood/log"""
    mood_score: int = Field(..., ge=1, le=10)
    mood_label: str = Field(..., min_length=1, max_length=50)


class MoodLogOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    mood_score: int
    mood_label: str
    logged_at: datetime

    model_config = {"from_attributes": True}


class MoodHistoryOut(BaseModel):
    """
    Chart-ready response for GET /mood/history.
    The React Native chart consumes `data_points` directly.
    """
    data_points: list[MoodLogOut]
    total: int
    page: int
    page_size: int