from sqlalchemy import Column, Date, DateTime, Integer, String, ForeignKey, SmallInteger, UniqueConstraint, func
from core.database import Base

class MoodCheckin(Base):
    __tablename__ = "mood_checkins"

    checkin_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    mood_score = Column(SmallInteger, nullable=False) # 1-10 scale
    mood_label = Column(String(30), nullable=False)   # e.g., "Happy", "Anxious"
    note = Column(String, nullable=True)
    checkin_date = Column(Date, nullable=False, default=func.current_date())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensures a user can't have two records for the same day at the DB level
    __table_args__ = (UniqueConstraint('user_id', 'checkin_date', name='_user_mood_day_uc'),)