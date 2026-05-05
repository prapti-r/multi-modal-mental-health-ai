import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class AiAnalysisResult(Base):
    """
    Maps 1:1 to a ChatMessage that contained media (voice or video).
    Stores all extracted ML features; the raw media file is deleted
    within MEDIA_RETENTION_MINUTES after this row is written.
    """
    __tablename__ = "ai_analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        unique=True,   # enforces 1:1
        nullable=False,
    )

    # Whisper speech-to-text transcript
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    # DeepFace output  
    facial_emotions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Librosa output  
    voice_features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # BERT/DistilRoBERTa output  
    text_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    model_version: Mapped[str] = mapped_column(
        String(20), default="v1.0.0", nullable=False
    )

    # Relationships 
    message: Mapped["ChatMessage"] = relationship( # type: ignore[name-defined]
        "ChatMessage", back_populates="ai_analysis"
    )

    def __repr__(self) -> str:
        return f"<AiAnalysisResult id={self.id} message_id={self.message_id}>"