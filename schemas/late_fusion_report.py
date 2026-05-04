import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class LateFusionReportOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    report_period_start: date
    report_period_end: date
    prediction_label: str
    qualitative_report: str
    is_crisis_flagged: bool
    # MHI: 0.0 (Crisis) → 1.0 (Stable)
    numerical_health_index: float = Field(..., ge=0.0, le=1.0)
    fusion_algorithm_version: str
    created_at: datetime

    model_config = {"from_attributes": True}

class FusionWeightsOut(BaseModel):
    """
    Documents which weight set was applied this week.
    Surfaced in the response so the frontend can show a 'data completeness' badge.
    """
    subjective:     float
    cognitive:      float
    physiological:  float | None = None   # None → fallback weights used
    fallback_used:  bool
 
 
class WeeklyReportOut(BaseModel):
    """
    Full response for GET /reports/weekly.
    Bundles the report + the weight set used + crisis flag at the top level
    so the client doesn't have to parse the qualitative text.
    """
    report:          LateFusionReportOut
    weights_applied: FusionWeightsOut
    # Convenience flag — True → show Crisis / Helpline screen immediately
    requires_crisis_intervention: bool
 