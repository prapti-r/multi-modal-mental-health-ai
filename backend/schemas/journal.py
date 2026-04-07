from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class JournalCreate(BaseModel):
    title: Optional[str] = None
    content: str
    entry_date: Optional[date] = None
    prompt_used: Optional[str] = None

class JournalResponse(BaseModel):
    entry_id: int
    title: Optional[str]
    content: str
    sentiment: Optional[str]
    entry_date: date
    created_at: datetime

    class Config:
        from_attributes = True
