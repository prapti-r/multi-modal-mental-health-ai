import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP

import datetime

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships 
    settings: Mapped["UserSettings"] = relationship(          # type: ignore[name-defined]
        "UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    otp_codes: Mapped[list["OtpCode"]] = relationship(        # type: ignore[name-defined]
        "OtpCode", back_populates="user", cascade="all, delete-orphan"
    )
    mood_logs: Mapped[list["MoodLog"]] = relationship(        # type: ignore[name-defined]
        "MoodLog", back_populates="user", cascade="all, delete-orphan"
    )
    journals: Mapped[list["Journal"]] = relationship(         # type: ignore[name-defined]
        "Journal", back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship( # type: ignore[name-defined]
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(   # type: ignore[name-defined]
        "Assessment", back_populates="user", cascade="all, delete-orphan"
    )
    risk_logs: Mapped[list["RiskLog"]] = relationship(        # type: ignore[name-defined]
        "RiskLog", back_populates="user", cascade="all, delete-orphan"
    )
    fusion_reports: Mapped[list["LateFusionReport"]] = relationship( # type: ignore[name-defined]
        "LateFusionReport", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"