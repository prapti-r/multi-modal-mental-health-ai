import uuid

from sqlalchemy import ForeignKey, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import datetime

from .base import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    # Brief AI-generated summary set at session end; nullable until then
    session_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships 
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions") # type: ignore[name-defined]
    messages: Mapped[list["ChatMessage"]] = relationship(                        # type: ignore[name-defined]
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id}>"