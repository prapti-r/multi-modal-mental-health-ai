import uuid
 
from sqlalchemy import Boolean, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
 
import datetime 

from .base import Base
 
 
class UserSettings(Base):
    __tablename__ = "user_settings"
 
    # One-to-one with users — user_id is both PK and FK
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    theme: Mapped[str] = mapped_column(
        String(20), default="light", nullable=False
    )  # 'light' | 'dark' | 'cozy' | 'minimal'
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    reminder_time: Mapped[datetime.time] = mapped_column(
        Time, default=datetime.time(20, 0), nullable=False
    )
    chatbot_tone: Mapped[str] = mapped_column(
        String(20), default="empathetic", nullable=False
    )  # 'empathetic' | 'direct' | 'friendly'
 
    #  Relationships 
    user: Mapped["User"] = relationship("User", back_populates="settings") # type: ignore[name-defined]
 
    def __repr__(self) -> str:
        return f"<UserSettings user_id={self.user_id} theme={self.theme!r}>"
 
