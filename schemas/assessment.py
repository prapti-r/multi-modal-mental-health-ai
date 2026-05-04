"""
schemas/assessment.py
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from models.assessment import TestType
from models.risk_log import RiskLevel


# PHQ-9: 0-27  |  GAD-7: 0-21
_MAX_SCORE: dict[TestType, int] = {
    TestType.PHQ9: 27,
    TestType.GAD7: 21,
}


class AssessmentCreate(BaseModel):
    """Payload for POST /assessments/submit"""
    test_type: TestType
    total_score: int = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_score_range(self) -> "AssessmentCreate":
        max_score = _MAX_SCORE[self.test_type]
        if self.total_score > max_score:
            raise ValueError(
                f"{self.test_type} score must be between 0 and {max_score}, "
                f"got {self.total_score}."
            )
        return self


class AssessmentOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    test_type: TestType
    total_score: int
    severity_label: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssessmentSubmitResponse(BaseModel):
    """
    Full response for POST /assessments/submit.
    Includes the assessment result AND the risk action taken,
    so the client knows immediately whether to show crisis resources.
    """
    assessment: AssessmentOut
    risk_level: RiskLevel
    risk_points: int
    action: str
    # True → client must show the Crisis / Emergency Helpline screen immediately
    requires_crisis_intervention: bool


class AssessmentHistoryOut(BaseModel):
    """Paginated response for GET /assessments/history"""
    entries: list[AssessmentOut]
    total: int
    page: int
    page_size: int