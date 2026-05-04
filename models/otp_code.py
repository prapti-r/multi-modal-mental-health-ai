import uuid

from sqlalchemy import Boolean, ForeignKey, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func, text

import datetime

from .base import Base


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Expires 10 minutes from creation — enforced at DB level
    expires_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW() + INTERVAL '10 minutes'"),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships 
    user: Mapped["User"] = relationship("User", back_populates="otp_codes") # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<OtpCode id={self.id} user_id={self.user_id} is_used={self.is_used}>"