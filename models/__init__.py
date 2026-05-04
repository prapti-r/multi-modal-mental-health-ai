# Import all models here so Alembic's env.py can discover them
# via: from models import Base

from .base import Base
from .user import User
from .user_settings import UserSettings
from .otp_code import OtpCode
from .mood_log import MoodLog
from .journal import Journal
from .chat_session import ChatSession
from .chat_message import ChatMessage
from .ai_analysis_result import AiAnalysisResult
from .assessment import Assessment
from .risk_log import RiskLog
from .late_fusion_report import LateFusionReport
from .therapist import Therapist

__all__ = [
    "Base",
    "User",
    "UserSettings",
    "OtpCode",
    "MoodLog",
    "Journal",
    "ChatSession",
    "ChatMessage",
    "AiAnalysisResult",
    "Assessment",
    "RiskLog",
    "LateFusionReport",
    "Therapist",
]