from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime

class AssessmentCreate(BaseModel):
    type: str                          # "PHQ-9" | "GAD-7"
    responses: Dict[str, int]          # { "q1": 2, "q2": 1, ... }


class AssessmentResponse(BaseModel):
    assessment_id: int
    type: str
    total_score: int
    severity_level: str
    completed_at: Any

    class Config:
        from_attributes = True

