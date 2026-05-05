"""
Assessment endpoints — all authenticated.

Routes:
    POST  /assessments/submit     Submit PHQ-9 or GAD-7, returns score + risk action
    GET   /assessments/history    Paginated assessment history
    GET   /risk/history           Risk log history (for the fusion model / developer view)

"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user_id
from schemas.assessment import (
    AssessmentCreate,
    AssessmentHistoryOut,
    AssessmentOut,
    AssessmentSubmitResponse,
)
from services import assessment_service

from sqlalchemy import func, select
from models.risk_log import RiskLog
from schemas.risk_log import RiskLogOut

router = APIRouter(tags=["Assessments & Risk"])
risk_router = APIRouter(tags=["Assessments & Risk"])


# Assessment 

@router.post(
    "/assessments/submit",
    response_model=AssessmentSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit PHQ-9 or GAD-7 assessment",
    description=(
        "Scores the submission using validated clinical bands, calculates risk points "
        "If `requires_crisis_intervention` is **true** in the response, the client "
        "must immediately display the Emergency Helplines and Therapist Directory."
    ),
)
async def submit_assessment(
    payload: AssessmentCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> AssessmentSubmitResponse:
    return await assessment_service.submit_assessment(db, user_id, payload)


@router.get(
    "/assessments/history",
    response_model=AssessmentHistoryOut,
    summary="Get assessment history",
    description="Returns all past PHQ-9 / GAD-7 results for the user, newest first.",
)
async def get_assessment_history(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=50, description="Records per page"),
) -> AssessmentHistoryOut:
    assessments, total = await assessment_service.get_history(
        db, user_id, page, page_size
    )
    return AssessmentHistoryOut(
        entries=[AssessmentOut.model_validate(a) for a in assessments],
        total=total,
        page=page,
        page_size=page_size,
    )


# Risk history

@risk_router.get(
    "/risk/history",
    summary="Get risk log history",
    description=(
        "Returns all risk_log entries for the authenticated user. "
        "Used by the weekly Late Fusion model and the developer dashboard."
    ),
)
async def get_risk_history(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
) -> dict:
    

    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count()).select_from(RiskLog).where(RiskLog.user_id == user_id)
    )
    total: int = total_result.scalar_one()

    data_result = await db.execute(
        select(RiskLog)
        .where(RiskLog.user_id == user_id)
        .order_by(RiskLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = list(data_result.scalars().all())

    return {
        "entries": [RiskLogOut.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }