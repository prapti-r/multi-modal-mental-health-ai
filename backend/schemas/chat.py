from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatMessageCreate(BaseModel):
    content: str
    session_id: Optional[int] = None   # None = start a new session


class ChatMessageResponse(BaseModel):
    message_id: int
    session_id: int
    role: str                           # "user" or "assistant"
    content: str
    text_emotion: Optional[str] = None
    crisis_flag: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    session_id: int
    user_id: int
    started_at: datetime
    message_count: int
    risk_flag: bool

    class Config:
        from_attributes = True