from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date


class MoodCheckinCreate(BaseModel):
    mood_score: int
    mood_label: str
    note: Optional[str] = None
    checkin_date: Optional[date] = None

    @field_validator("mood_score")
    @classmethod
    def score_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("Mood score must be between 1 and 10")
        return v


class MoodCheckinResponse(BaseModel):
    checkin_id: int
    user_id: int
    mood_score: int
    mood_label: str
    note: Optional[str]
    checkin_date: date

    class Config:
        from_attributes = True