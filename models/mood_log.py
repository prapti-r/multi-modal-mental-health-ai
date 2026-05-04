import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import datetime

from .base import Base


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Score constrained 1-10 at the DB level
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    mood_label: Mapped[str] = mapped_column(String(50), nullable=False)
    logged_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("mood_score BETWEEN 1 AND 10", name="ck_mood_score_range"),
    )

    #  Relationships 
    user: Mapped["User"] = relationship("User", back_populates="mood_logs") # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<MoodLog id={self.id} score={self.mood_score} label={self.mood_label!r}>"