from sqlalchemy import Column, Date, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY
from core.database import Base

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    entry_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=True)
    # Match the PostgreSQL TEXT[] type from your schema
    emotion_tags = Column(ARRAY(String), nullable=True)
    prompt_used = Column(Text, nullable=True)
    entry_date = Column(Date, nullable=False, default=func.current_date())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())