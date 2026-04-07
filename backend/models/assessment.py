from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, SmallInteger, func
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    type = Column(String(20), nullable=False) # PHQ-9 / GAD-7
    responses = Column(JSONB, nullable=False)
    total_score = Column(SmallInteger, nullable=False)
    severity_level = Column(String(20), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())