import uuid
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import datetime

from .base import Base


class TestType(str, enum.Enum):
    PHQ9 = "PHQ-9"
    GAD7 = "GAD-7"


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_type: Mapped[TestType] = mapped_column(
        Enum(TestType, name="test_type_enum"), nullable=False
    )
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    # e.g. "Minimal" | "Mild" | "Moderate" | "Moderately Severe" | "Severe"
    severity_label: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships 
    user: Mapped["User"] = relationship("User", back_populates="assessments") # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<Assessment id={self.id} type={self.test_type} "
            f"score={self.total_score} severity={self.severity_label!r}>"
        )