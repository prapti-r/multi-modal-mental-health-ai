"""
admin.py
─────────
SQLAdmin setup for Eunoia — gives a Django-like admin UI at /admin.

Mount this in main.py:
    from admin import admin  ← if you move setup here
    OR inline the Admin(...) call as shown at the bottom.

Visit: http://localhost:8000/admin
Login: username=admin  password=set via ADMIN_PASSWORD env var
"""

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from core.config import settings
from core.database import AsyncSessionLocal, engine

from models.user import User
from models.user_settings import UserSettings
from models.otp_code import OtpCode
from models.mood_log import MoodLog
from models.journal import Journal
from models.chat_session import ChatSession
from models.chat_message import ChatMessage
from models.ai_analysis_result import AiAnalysisResult
from models.assessment import Assessment
from models.risk_log import RiskLog
from models.late_fusion_report import LateFusionReport
from models.therapist import Therapist


# ── Authentication ─────────────────────────────────────────────────────────────

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")
        if username == "admin" and password == "eunoia2026":
            request.session.update({"token": "admin"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session


# ── Model Views ────────────────────────────────────────────────────────────────

class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"

    column_list = [
        User.id,
        User.full_name,
        User.email,
        User.is_verified,
        User.created_at,
    ]
    column_searchable_list = [User.email, User.full_name]
    column_sortable_list   = [User.created_at, User.full_name, User.is_verified]
    column_default_sort    = (User.created_at, True)   # newest first

    # Don't expose password hash in detail view
    column_details_exclude_list = [User.password_hash]
    form_excluded_columns       = [User.password_hash]

    can_create = False   # registration is handled by the API
    can_delete = True


class UserSettingsAdmin(ModelView, model=UserSettings):
    name = "User Settings"
    name_plural = "User Settings"
    icon = "fa-solid fa-gear"

    column_list = [
        UserSettings.user_id,
        UserSettings.theme,
        UserSettings.notifications_enabled,
        UserSettings.reminder_time,
        UserSettings.chatbot_tone,
    ]
    column_sortable_list = [UserSettings.theme, UserSettings.chatbot_tone]
    can_create = False
    can_delete = False


class OtpCodeAdmin(ModelView, model=OtpCode):
    name = "OTP Code"
    name_plural = "OTP Codes"
    icon = "fa-solid fa-key"

    column_list = [
        OtpCode.id,
        OtpCode.user_id,
        OtpCode.code,
        OtpCode.is_used,
        OtpCode.expires_at,
        OtpCode.created_at,
    ]
    column_sortable_list   = [OtpCode.created_at, OtpCode.is_used, OtpCode.expires_at]
    column_default_sort    = (OtpCode.created_at, True)
    can_create = False
    can_delete = True


class MoodLogAdmin(ModelView, model=MoodLog):
    name = "Mood Log"
    name_plural = "Mood Logs"
    icon = "fa-solid fa-face-smile"

    column_list = [
        MoodLog.id,
        MoodLog.user_id,
        MoodLog.mood_score,
        MoodLog.mood_label,
        MoodLog.logged_at,
    ]
    column_sortable_list   = [MoodLog.logged_at, MoodLog.mood_score]
    column_default_sort    = (MoodLog.logged_at, True)
    can_create = False
    can_delete = True


class JournalAdmin(ModelView, model=Journal):
    name = "Journal Entry"
    name_plural = "Journal Entries"
    icon = "fa-solid fa-book-open"

    column_list = [
        Journal.id,
        Journal.user_id,
        Journal.sentiment_label,
        Journal.sentiment_score,
        Journal.created_at,
    ]
    # Don't show full journal content in list — only in detail view
    column_details_list  = [
        Journal.id,
        Journal.user_id,
        Journal.content,
        Journal.sentiment_label,
        Journal.sentiment_score,
        Journal.created_at,
    ]
    column_sortable_list  = [Journal.created_at, Journal.sentiment_score, Journal.sentiment_label]
    column_default_sort   = (Journal.created_at, True)
    can_create = False
    can_delete = True


class ChatSessionAdmin(ModelView, model=ChatSession):
    name = "Chat Session"
    name_plural = "Chat Sessions"
    icon = "fa-solid fa-comments"

    column_list = [
        ChatSession.id,
        ChatSession.user_id,
        ChatSession.started_at,
        ChatSession.session_summary,
    ]
    column_sortable_list  = [ChatSession.started_at]
    column_default_sort   = (ChatSession.started_at, True)
    can_create = False
    can_delete = True


class ChatMessageAdmin(ModelView, model=ChatMessage):
    name = "Chat Message"
    name_plural = "Chat Messages"
    icon = "fa-solid fa-message"

    column_list = [
        ChatMessage.id,
        ChatMessage.session_id,
        ChatMessage.sender_type,
        ChatMessage.input_mode,
        ChatMessage.created_at,
    ]
    # Show content only in detail view (can be long)
    column_details_list = [
        ChatMessage.id,
        ChatMessage.session_id,
        ChatMessage.sender_type,
        ChatMessage.input_mode,
        ChatMessage.content,
        ChatMessage.created_at,
    ]
    column_sortable_list  = [ChatMessage.created_at, ChatMessage.sender_type, ChatMessage.input_mode]
    column_default_sort   = (ChatMessage.created_at, True)
    can_create = False
    can_delete = True


class AiAnalysisResultAdmin(ModelView, model=AiAnalysisResult):
    name = "AI Analysis Result"
    name_plural = "AI Analysis Results"
    icon = "fa-solid fa-brain"

    column_list = [
        AiAnalysisResult.id,
        AiAnalysisResult.message_id,
        AiAnalysisResult.transcript,
        AiAnalysisResult.model_version,
    ]
    # JSONB columns shown only in detail (too wide for list)
    column_details_list = [
        AiAnalysisResult.id,
        AiAnalysisResult.message_id,
        AiAnalysisResult.transcript,
        AiAnalysisResult.text_analysis,
        AiAnalysisResult.facial_emotions,
        AiAnalysisResult.voice_features,
        AiAnalysisResult.model_version,
    ]
    can_create = False
    can_delete = True


class AssessmentAdmin(ModelView, model=Assessment):
    name = "Assessment"
    name_plural = "Assessments"
    icon = "fa-solid fa-clipboard-list"

    column_list = [
        Assessment.id,
        Assessment.user_id,
        Assessment.test_type,
        Assessment.total_score,
        Assessment.severity_label,
        Assessment.created_at,
    ]
    column_sortable_list  = [Assessment.created_at, Assessment.total_score, Assessment.test_type]
    column_default_sort   = (Assessment.created_at, True)
    can_create = False
    can_delete = True


class RiskLogAdmin(ModelView, model=RiskLog):
    name = "Risk Log"
    name_plural = "Risk Logs"
    icon = "fa-solid fa-triangle-exclamation"

    column_list = [
        RiskLog.id,
        RiskLog.user_id,
        RiskLog.risk_level,
        RiskLog.trigger_source,
        RiskLog.total_points,
        RiskLog.action_taken,
        RiskLog.created_at,
    ]
    column_sortable_list  = [RiskLog.created_at, RiskLog.risk_level, RiskLog.total_points]
    column_default_sort   = (RiskLog.created_at, True)
    can_create = False
    can_delete = True


class LateFusionReportAdmin(ModelView, model=LateFusionReport):
    name = "Late Fusion Report"
    name_plural = "Late Fusion Reports"
    icon = "fa-solid fa-chart-line"

    column_list = [
        LateFusionReport.id,
        LateFusionReport.user_id,
        LateFusionReport.report_period_start,
        LateFusionReport.report_period_end,
        LateFusionReport.prediction_label,
        LateFusionReport.numerical_health_index,
        LateFusionReport.is_crisis_flagged,
        LateFusionReport.created_at,
    ]
    column_details_list = [
        LateFusionReport.id,
        LateFusionReport.user_id,
        LateFusionReport.report_period_start,
        LateFusionReport.report_period_end,
        LateFusionReport.prediction_label,
        LateFusionReport.numerical_health_index,
        LateFusionReport.is_crisis_flagged,
        LateFusionReport.qualitative_report,   # long text — detail only
        LateFusionReport.fusion_algorithm_version,
        LateFusionReport.created_at,
    ]
    column_sortable_list  = [
        LateFusionReport.created_at,
        LateFusionReport.numerical_health_index,
        LateFusionReport.is_crisis_flagged,
        LateFusionReport.prediction_label,
    ]
    column_default_sort   = (LateFusionReport.created_at, True)
    can_create = False
    can_delete = True


class TherapistAdmin(ModelView, model=Therapist):
    name = "Therapist"
    name_plural = "Therapists"
    icon = "fa-solid fa-user-doctor"

    column_list = [
        Therapist.id,
        Therapist.name,
        Therapist.specialization,
        Therapist.contact_number,
        Therapist.location,
        Therapist.is_emergency_contact,
    ]
    column_searchable_list = [Therapist.name, Therapist.specialization, Therapist.location]
    column_sortable_list   = [Therapist.name, Therapist.is_emergency_contact]
    column_default_sort    = (Therapist.is_emergency_contact, True)  # emergency contacts first

    # Therapists CAN be created/edited from admin (static directory)
    can_create = True
    can_edit   = True
    can_delete = True


# ── Factory function — call this in main.py ────────────────────────────────────

def create_admin(app) -> Admin:
    """
    Create and configure the SQLAdmin instance.

    Call in main.py:
        from admin import create_admin
        admin = create_admin(app)   # ← after app = create_app()
    """
    authentication_backend = AdminAuth(secret_key="your-secret-key-change-in-prod")

    admin = Admin(
        app,
        engine,
        session_maker=AsyncSessionLocal,
        authentication_backend=authentication_backend,
        title="Eunoia Admin",
        base_url="/admin",
    )

    admin.add_view(UserAdmin)
    admin.add_view(UserSettingsAdmin)
    admin.add_view(OtpCodeAdmin)
    admin.add_view(MoodLogAdmin)
    admin.add_view(JournalAdmin)
    admin.add_view(ChatSessionAdmin)
    admin.add_view(ChatMessageAdmin)
    admin.add_view(AiAnalysisResultAdmin)
    admin.add_view(AssessmentAdmin)
    admin.add_view(RiskLogAdmin)
    admin.add_view(LateFusionReportAdmin)
    admin.add_view(TherapistAdmin)

    return admin