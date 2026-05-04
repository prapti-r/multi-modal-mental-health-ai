import uuid
from datetime import time
from typing import Literal

from pydantic import BaseModel, Field


class UserSettingsOut(BaseModel):
    user_id: uuid.UUID
    theme: str
    notifications_enabled: bool
    reminder_time: time
    chatbot_tone: str

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    """Payload for PUT /user/settings"""
    theme: Literal["light", "dark", "cozy", "minimal"] | None = None
    notifications_enabled: bool | None = None
    reminder_time: time | None = None
    chatbot_tone: Literal["empathetic", "direct", "friendly"] | None = None