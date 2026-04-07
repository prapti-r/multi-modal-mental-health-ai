from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(Integer, default=0)
    overall_emotion = Column(String(30), nullable=True)
    risk_flag = Column(Boolean, default=False)

    # Relationship to messages
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    role = Column(String(10), nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    text_emotion = Column(String(30), nullable=True)
    text_sentiment = Column(String(20), nullable=True)
    intent_label = Column(String(50), nullable=True)
    crisis_flag = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")