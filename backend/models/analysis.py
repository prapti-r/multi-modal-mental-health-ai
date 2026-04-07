from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from core.database import Base

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    
    prediction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"), nullable=True)
    risk_score = Column(Numeric(5, 4), nullable=False)
    risk_level = Column(String(20), nullable=False)
    model_used = Column(String(50), nullable=True)
    trigger_factors = Column(ARRAY(String), nullable=True)
    intervention_sent = Column(Boolean, default=False)
    predicted_at = Column(DateTime, server_default=func.now())

class EmotionAnalysisResult(Base):
    __tablename__ = "emotion_analysis_results"
    
    analysis_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"), nullable=True)
    modality = Column(String(10), nullable=False) # text, voice, face
    detected_emotion = Column(String(30), nullable=False)
    emotion_scores = Column(JSONB, nullable=True)
    fused_emotion = Column(String(30), nullable=True)
    model_used = Column(String(50), nullable=True)
    analyzed_at = Column(DateTime, server_default=func.now())