"""
schemas/chat.py
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from models.chat_message import InputMode, SenderType
from models.risk_log import RiskLevel


# Session

class ChatSessionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    started_at: datetime
    session_summary: str | None

    model_config = {"from_attributes": True}


class ChatSessionListOut(BaseModel):
    """Paginated response for GET /chat/sessions"""
    sessions: list[ChatSessionOut]
    total: int
    page: int
    page_size: int


# Analysis result 

class AiAnalysisResultOut(BaseModel):
    """Embedded in ChatMessageOut when the message had media attached."""
    transcript:      str | None
    facial_emotions: dict[str, Any] | None
    voice_features:  dict[str, Any] | None
    text_analysis:   dict[str, Any] | None
    model_version:   str

    model_config = {"from_attributes": True}


# Message

class ChatMessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    sender_type: SenderType
    content: str
    input_mode: InputMode
    created_at: datetime
    ai_analysis: AiAnalysisResultOut | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessagePairOut(BaseModel):
    """
    Returned by both POST /chat/message and POST /chat/message/media.
    Bundles the user message and the AI reply in a single response so the
    client can render both immediately without a second fetch.
    Also surfaces the risk_level so the client knows whether to show
    crisis resources without waiting for the next assessment cycle.
    """
    user_message:  ChatMessageOut
    ai_message:    ChatMessageOut
    risk_level:    RiskLevel
    used_fallback: bool = Field(
        False,
        description="True when the ML pipeline failed and CBT templates were used instead.",
    )


# Text message request

class TextMessageCreate(BaseModel):
    """Payload for POST /chat/message (text-only path)."""
    session_id: uuid.UUID
    content: str = Field(..., min_length=1, max_length=4000)


# Cursor-paginated message history 

class MessageHistoryOut(BaseModel):
    """
    Cursor-based pagination response for GET /chat/sessions/{id}/messages.

    Pass `next_cursor` as `?cursor=<value>` in the next request to fetch
    the previous page. When next_cursor is null, there are no older messages.
    """
    messages:    list[ChatMessageOut]
    next_cursor: datetime | None = Field(
        None,
        description="Timestamp cursor — pass as ?cursor= to fetch older messages.",
    )
    session_id: uuid.UUID