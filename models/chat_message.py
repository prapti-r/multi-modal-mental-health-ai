import uuid
import enum

from sqlalchemy import Enum, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import datetime

from .base import Base


class SenderType(str, enum.Enum):
    USER = "user"
    AI = "ai"


class InputMode(str, enum.Enum):
    TEXT = "text"
    VOICE = "voice"
    VIDEO = "video"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type: Mapped[SenderType] = mapped_column(
        Enum(SenderType, name="sender_type_enum"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    input_mode: Mapped[InputMode] = mapped_column(
        Enum(InputMode, name="input_mode_enum"), nullable=False, default=InputMode.TEXT
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships 
    session: Mapped["ChatSession"] = relationship(          # type: ignore[name-defined]
        "ChatSession", back_populates="messages"
    )
    ai_analysis: Mapped["AiAnalysisResult | None"] = relationship( # type: ignore[name-defined]
        "AiAnalysisResult", back_populates="message", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} sender={self.sender_type} mode={self.input_mode}>"