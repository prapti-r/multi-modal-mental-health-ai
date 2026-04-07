from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from models.analysis import EmotionAnalysisResult, RiskPrediction
from schemas.emotion import EmotionResult, FusionInput

router = APIRouter(prefix="/emotion", tags=["Emotion Analysis"])

#  POST /emotion/text 
@router.post("/text", response_model=EmotionResult)
def analyze_text_emotion(
    text: str = Form(...),
    session_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Stub logic for DistilRoBERTa
    detected = "neutral"
    scores = {"neutral": 0.7, "sadness": 0.2, "joy": 0.1}
    model = "DistilRoBERTa-v1"

    # Save to Database
    analysis_record = EmotionAnalysisResult(
        user_id=current_user.user_id,
        session_id=session_id,
        modality="text",
        detected_emotion=detected,
        emotion_scores=scores,
        model_used=model
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)
    
    return analysis_record

#  POST /emotion/voice 
@router.post("/voice", response_model=EmotionResult)
async def analyze_voice_emotion(
    audio: UploadFile = File(...),
    session_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if audio.content_type not in ["audio/mpeg", "audio/wav", "audio/m4a", "audio/ogg"]:
        raise HTTPException(status_code=400, detail="Audio file required (wav/mp3/m4a)")

    # Stub logic for CNN-LSTM
    detected = "neutral"
    scores = {"neutral": 0.6, "sadness": 0.3, "anger": 0.1}
    
    analysis_record = EmotionAnalysisResult(
        user_id=current_user.user_id,
        session_id=session_id,
        modality="voice",
        detected_emotion=detected,
        emotion_scores=scores,
        model_used="CNN-LSTM-v1"
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)
    
    return analysis_record


#  POST /emotion/face 
@router.post("/face", response_model=EmotionResult)
async def analyze_face_emotion(
    image: UploadFile = File(...),
    session_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Image file required (jpg/png)")

    # Stub logic for DeepFace
    detected = "neutral"
    scores = {"neutral": 0.5, "happy": 0.3, "sad": 0.2}

    analysis_record = EmotionAnalysisResult(
        user_id=current_user.user_id,
        session_id=session_id,
        modality="face",
        detected_emotion=detected,
        emotion_scores=scores,
        model_used="DeepFace-v2"
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)
    
    return analysis_record

@router.post("/fuse", response_model=EmotionResult)
def late_fusion(
    payload: FusionInput, 
    session_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    votes = [payload.text_emotion, payload.voice_emotion, payload.face_emotion]
    fused = max(set(votes), key=votes.count)

    analysis_record = EmotionAnalysisResult(
        user_id=current_user.user_id,
        session_id=session_id,
        modality="fused",
        detected_emotion=fused,
        fused_emotion=fused,
        emotion_scores={"confidence": 0.95}, # Example score
        model_used="LateFusion-MajorityVote"
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)
    
    return analysis_record

# Risk Assessment
@router.get("/risk-assessments/latest", response_model=None)
def get_latest_risk(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # This queries the table you provided in models
    risk = db.query(RiskPrediction).filter(
        RiskPrediction.user_id == current_user.user_id
    ).order_by(RiskPrediction.predicted_at.desc()).first()
    
    if not risk:
        raise HTTPException(status_code=404, detail="No risk assessment found")
    return risk