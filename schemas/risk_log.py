import uuid
from datetime import datetime

from pydantic import BaseModel

from models.risk_log import RiskLevel


class RiskLogOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    risk_level: RiskLevel
    trigger_source: str
    total_points: int
    action_taken: str
    created_at: datetime

    model_config = {"from_attributes": True}