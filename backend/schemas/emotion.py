from pydantic import BaseModel
from typing import Optional, Dict

class EmotionResult(BaseModel):
    model_config = {'protected_namespaces': ()}
    
    modality: str
    detected_emotion: str
    emotion_scores: Dict[str, float]
    fused_emotion: Optional[str] = None
    model_used: str

class FusionInput(BaseModel):
    text_emotion: str
    voice_emotion: str
    face_emotion: str

