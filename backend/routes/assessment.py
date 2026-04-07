from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from models.assessment import Assessment
from schemas.assessment import AssessmentCreate, AssessmentResponse

router = APIRouter(prefix="/assessments", tags=["Assessments"])

# Scoring helpers 
SCORING = {
    "PHQ-9": [
        (0, 4,   "Minimal"),
        (5, 9,   "Mild"),
        (10, 14, "Moderate"),
        (15, 19, "Moderately Severe"),
        (20, 27, "Severe"),
    ],
    "GAD-7": [
        (0, 4,  "Minimal"),
        (5, 9,  "Mild"),
        (10, 14, "Moderate"),
        (15, 21, "Severe"),
    ],
}


def score_to_severity(assessment_type: str, score: int) -> str:
    for low, high, label in SCORING.get(assessment_type.upper(), []):
        if low <= score <= high:
            return label
    return "Unknown"


# POST /assessment/ 
@router.post("/", response_model=AssessmentResponse, status_code=201)
def submit_assessment(
    payload: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    allowed = ["PHQ-9", "GAD-7"]
    if payload.type.upper() not in [a.upper() for a in allowed]:
        raise HTTPException(status_code=400, detail=f"Assessment type must be one of {allowed}")

    total = sum(payload.responses.values())
    severity = score_to_severity(payload.type, total)

    record = Assessment(
        user_id=current_user.user_id,
        type=payload.type.upper(),
        responses=payload.responses,
        total_score=total,
        severity_level=severity,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


#  GET /assessment/ 
@router.get("/", response_model=List[AssessmentResponse])
def get_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.user_id)
        .order_by(Assessment.completed_at.desc())
        .all()
    )


#  GET /assessment/latest 
@router.get("/latest", response_model=AssessmentResponse)
def get_latest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    record = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.user_id)
        .order_by(Assessment.completed_at.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No assessments found")
    return record