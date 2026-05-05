"""
Assessment submission, severity scoring, and risk evaluation.

Risk Thresholds:
    Mild     (0-30):  Standard CBT interaction
    Moderate (31-59):  Suggest breathing / formal assessment
    Severe   (>=60):    Hard trigger — show emergency helplines

"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import NotFoundError
from models.assessment import Assessment, TestType
from models.risk_log import RiskLog, RiskLevel
from schemas.assessment import AssessmentCreate, AssessmentOut, AssessmentSubmitResponse


# Scoring tables (clinical standards) 

# PHQ-9 severity bands  (Kroenke & Spitzer, 2002)
_PHQ9_BANDS: list[tuple[int, str]] = [
    (4,  "Minimal"),
    (9,  "Mild"),
    (14, "Moderate"),
    (19, "Moderately Severe"),
    (27, "Severe"),
]

# GAD-7 severity bands  (Spitzer et al., 2006)
_GAD7_BANDS: list[tuple[int, str]] = [
    (4,  "Minimal"),
    (9,  "Mild"),
    (14, "Moderate"),
    (21, "Severe"),
]

_SCORE_BANDS: dict[TestType, list[tuple[int, str]]] = {
    TestType.PHQ9: _PHQ9_BANDS,
    TestType.GAD7: _GAD7_BANDS,
}

# clinical assessment hard trigger
_ASSESSMENT_HARD_TRIGGER_SCORE = 15
_ASSESSMENT_RISK_POINTS = 40


# Internal helpers 

def _get_severity_label(test_type: TestType, score: int) -> str:
    """
    Map a raw score to a severity label using clinical band tables.
    Returns the label of the first band whose ceiling the score does not exceed.
    """
    for ceiling, label in _SCORE_BANDS[test_type]:
        if score <= ceiling:
            return label
    return "Severe"  # fallback — score exceeded all defined ceilings


def _calculate_risk_points(score: int) -> int:
    """
    Return risk points contributed by this assessment
    40 points if score ≥ 15, otherwise 0.
    """
    return _ASSESSMENT_RISK_POINTS if score >= _ASSESSMENT_HARD_TRIGGER_SCORE else 0


def _get_risk_level(total_points: int) -> RiskLevel:
    """
    Classify a point total into a risk tier using risk thresholds.
    """
    if total_points >= settings.RISK_SEVERE_THRESHOLD:
        return RiskLevel.SEVERE
    if total_points >= settings.RISK_MODERATE_THRESHOLD:
        return RiskLevel.MODERATE
    return RiskLevel.MILD


def _get_action(risk_level: RiskLevel) -> str:
    """
    Return the action string logged to risk_logs and surfaced to the client.
    """
    actions = {
        RiskLevel.MILD:     "Standard empathetic CBT response provided.",
        RiskLevel.MODERATE: "De-escalation tools suggested (breathing exercise / formal assessment).",
        RiskLevel.SEVERE:   "Displayed Emergency Helplines and Therapist Directory.",
    }
    return actions[risk_level]


# service functions 

async def submit_assessment(
    db: AsyncSession,
    user_id: UUID,
    payload: AssessmentCreate,
) -> AssessmentSubmitResponse:
    """
    Persist an assessment, compute severity + risk, log the risk event,
    and return a unified response the route can pass directly to the client.

    The client checks `requires_crisis_intervention` to decide whether to
    immediately navigate to the Crisis screen .
    """
    # Severity label
    severity_label = _get_severity_label(payload.test_type, payload.total_score)

    # Risk points from this assessment
    risk_points = _calculate_risk_points(payload.total_score)

    # Risk level + action
    risk_level = _get_risk_level(risk_points)
    action = _get_action(risk_level)

    # Persist assessment
    assessment = Assessment(
        user_id=user_id,
        test_type=payload.test_type,
        total_score=payload.total_score,
        severity_label=severity_label,
    )
    db.add(assessment)
    await db.flush()  # populate assessment.id

    # Always log the risk event — Mild entries still feed the weekly fusion model
    risk_log = RiskLog(
        user_id=user_id,
        risk_level=risk_level,
        trigger_source=f"{payload.test_type.value} Assessment",
        total_points=risk_points,
        action_taken=action,
    )
    db.add(risk_log)
    await db.flush()

    # Build response
    assessment_out = AssessmentOut.model_validate(assessment)
    return AssessmentSubmitResponse(
        assessment=assessment_out,
        risk_level=risk_level,
        risk_points=risk_points,
        action=action,
        requires_crisis_intervention=(risk_level == RiskLevel.SEVERE),
    )


async def get_history(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Assessment], int]:
    """
    Return paginated assessment history, newest first.

    Returns:
        (assessments, total_count)
    """
    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count())
        .select_from(Assessment)
        .where(Assessment.user_id == user_id)
    )
    total: int = total_result.scalar_one()

    data_result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    assessments = list(data_result.scalars().all())

    return assessments, total