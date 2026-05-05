import uuid
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

import datetime

from .base import Base


class RiskLevel(str, enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class RiskLog(Base):
    __tablename__ = "risk_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level_enum"), nullable=False
    )
   
    trigger_source: Mapped[str] = mapped_column(String(255), nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False)
   
    action_taken: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships 
    user: Mapped["User"] = relationship("User", back_populates="risk_logs") # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<RiskLog id={self.id} level={self.risk_level} "
            f"points={self.total_points} source={self.trigger_source!r}>"
        )