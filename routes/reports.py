"""
routes/reports.py
──────────────────
Weekly Late Fusion report and therapist directory — all authenticated.

Routes:
    GET  /reports/weekly    Fetch (or generate) this week's MHI report
    GET  /therapists        Fetch the full therapist directory
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user_id
from schemas.late_fusion_report import (
    FusionWeightsOut,
    LateFusionReportOut,
    WeeklyReportOut,
)
from schemas.therapist import (
    TherapistListOut,
    TherapistOut,
)
from services import report_service
from services.report_service import (
    _W_COGNITIVE,
    _W_COGN_FALLBACK,
    _W_PHYSIOLOGICAL,
    _W_SUBJECTIVE,
    _W_SUBJ_FALLBACK,
)

# services/report_service.py — add this near the weight constants:
STANDARD_WEIGHTS = {"subjective": 0.40, "cognitive": 0.35, "physiological": 0.25}
FALLBACK_WEIGHTS = {"subjective": _W_SUBJ_FALLBACK, "cognitive": _W_COGN_FALLBACK}

router = APIRouter(tags=["Reports & Therapists"])


@router.get(
    "/reports/weekly",
    response_model=WeeklyReportOut,
    summary="Get weekly Late Fusion report",
    description=(
        "Returns the current ISO week's Mental Health Index (MHI) and qualitative "
        "wellbeing report. The report is generated on first request for the week "
        "and cached — subsequent calls return the same report until the next Monday. "
        "\n\n"
        "**MHI formula (PRD §7.2):** `1.0 − clamp(avg_daily_risk_pts / 100, 0, 1)`\n\n"
        "**Channel weights (PRD §7.3):** Subjective 40% · Cognitive 35% · Physiological 25%\n\n"
        "If no voice/video check-ins were logged this week, physiological weight is "
        "redistributed proportionally (Subjective → 53.3%, Cognitive → 46.7%).\n\n"
        "Check `requires_crisis_intervention` — if True, navigate to the Crisis screen."
    ),
)
async def get_weekly_report(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> WeeklyReportOut:
    report = await report_service.get_or_generate_weekly_report(db, user_id)

    # Determine which weights were applied by checking whether the qualitative
    # report mentions the fallback note (no physiological data available).
    # The cleaner production approach would be to store this on the model,
    # but for v1 we derive it from the physiological weight signal.
    physiological_data_present = (
        "No voice or video check-ins" not in report.qualitative_report
    )

    if physiological_data_present:
        weights = FusionWeightsOut(
            subjective=_W_SUBJECTIVE,
            cognitive=_W_COGNITIVE,
            physiological=_W_PHYSIOLOGICAL,
            fallback_used=False,
        )
    else:
        weights = FusionWeightsOut(
            subjective=_W_SUBJ_FALLBACK,
            cognitive=_W_COGN_FALLBACK,
            physiological=None,
            fallback_used=True,
        )

    return WeeklyReportOut(
        report=LateFusionReportOut.model_validate(report),
        weights_applied=weights,
        requires_crisis_intervention=report.is_crisis_flagged,
    )


@router.get(
    "/therapists",
    response_model=TherapistListOut,
    summary="Get therapist directory",
    description=(
        "Returns the full directory of mental health professionals. "
        "Emergency contacts (`is_emergency_contact=true`) are sorted first — "
        "these appear at the top of the Severe Risk / Crisis screen (PRD §3.2)."
    ),
)
async def get_therapists(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TherapistListOut:
    therapists = await report_service.get_therapists(db)
    return TherapistListOut(
        therapists=[TherapistOut.model_validate(t) for t in therapists],
        total=len(therapists),
    )