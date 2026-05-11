import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import settings
from core.exceptions import ForbiddenError, MediaProcessingError, NotFoundError
from ml import bert_classifier, media_processor
from ml.bert_classifier import TextAnalysisResult
from ml.cbt_templates import (
    get_cbt_response,
    get_crisis_response,
    get_fallback_response,
    get_moderate_risk_response,
)
from ml.media_processor import MediaAnalysisOutput, check_physiological_distress
from models.ai_analysis_result import AiAnalysisResult
from models.chat_message import ChatMessage, InputMode, SenderType
from models.chat_session import ChatSession
from models.risk_log import RiskLog, RiskLevel

# define logger — was used in except block but never imported
logger = logging.getLogger(__name__)

# Risk point constants
_RISK_PTS_CRISIS_CHAT   = 40
_RISK_PTS_HOPELESSNESS  = 20
_RISK_PTS_PHYSIOLOGICAL = 20
_SAFETY_OVERRIDE_THRESHOLD = 0.40

_MIME_NORMALISATION = {
    "audio/3gp":       "audio/mpeg",
    "audio/x-m4a":     "audio/mpeg",
    "audio/mp4":       "audio/mpeg",
    "audio/m4a":       "audio/mpeg",
    "audio/aac":       "audio/mpeg",
    "audio/x-wav":     "audio/wav",  
    "video/quicktime": "video/mp4",
}

def _normalise_content_type(content_type: str) -> str:
    """Map mobile-specific MIME types to backend-accepted equivalents."""
    return _MIME_NORMALISATION.get(content_type, content_type)


@dataclass
class ChatMessagePair:
    user_message:  ChatMessage
    ai_message:    ChatMessage
    risk_level:    RiskLevel
    used_fallback: bool


async def _require_session(
    db: AsyncSession, session_id: UUID, user_id: UUID
) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("Chat session not found.")
    if session.user_id != user_id:
        raise ForbiddenError("You do not have access to this chat session.")
    return session


def _get_risk_level(points: int) -> RiskLevel:
    if points >= settings.RISK_SEVERE_THRESHOLD:
        return RiskLevel.SEVERE
    if points >= settings.RISK_MODERATE_THRESHOLD:
        return RiskLevel.MODERATE
    return RiskLevel.MILD


def _apply_safety_override(
    bert_result: TextAnalysisResult | None,
    message_points: int,
) -> tuple[int, RiskLevel, bool]:
    if bert_result is None:
        return message_points, _get_risk_level(message_points), False
    suicidal_score = bert_result.all_scores.get("suicidal", 0.0)
    if suicidal_score >= _SAFETY_OVERRIDE_THRESHOLD:
        forced_points = max(message_points, settings.RISK_SEVERE_THRESHOLD)
        return forced_points, RiskLevel.SEVERE, True
    return message_points, _get_risk_level(message_points), False


def _get_action_string(risk_level: RiskLevel) -> str:
    return {
        RiskLevel.MILD:     "Standard empathetic CBT response provided.",
        RiskLevel.MODERATE: "De-escalation tools suggested.",
        RiskLevel.SEVERE:   "Displayed Emergency Helplines and Therapist Directory.",
    }[risk_level]


async def _log_risk(
    db: AsyncSession,
    user_id: UUID,
    risk_level: RiskLevel,
    trigger_source: str,
    total_points: int,
) -> None:
    db.add(RiskLog(
        user_id=user_id,
        risk_level=risk_level,
        trigger_source=trigger_source,
        total_points=total_points,
        action_taken=_get_action_string(risk_level),
    ))
    await db.flush()


def _pick_ai_response(
    risk_level: RiskLevel,
    emotion_label: str,
    used_fallback: bool,
    user_content: str,
) -> str:
    if risk_level == RiskLevel.SEVERE:
        return get_crisis_response()
    if risk_level == RiskLevel.MODERATE:
        return get_moderate_risk_response()
    if used_fallback:
        return get_fallback_response(user_content)
    return get_cbt_response(emotion_label, user_text=user_content)


def _build_text_analysis_dict(bert_result: TextAnalysisResult) -> dict:
    return {
        "label": bert_result.label,
        "score": bert_result.score,
        "raw_label": bert_result.raw_label,
        "is_crisis": bert_result.is_crisis,
        "is_deep_hopelessness": bert_result.is_deep_hopelessness,
        "all_scores": bert_result.all_scores,
    }


async def _persist_message_pair(
    db: AsyncSession,
    session_id: UUID,
    user_content: str,
    input_mode: InputMode,
    ai_content: str,
    analysis_output: MediaAnalysisOutput | None = None,
) -> tuple[ChatMessage, ChatMessage]:
    user_msg = ChatMessage(
        session_id=session_id,
        sender_type=SenderType.USER,
        content=user_content,
        input_mode=input_mode,
    )
    db.add(user_msg)
    await db.flush()

    analysis_row: AiAnalysisResult | None = None
    if analysis_output is not None:
        analysis_row = AiAnalysisResult(
            message_id=user_msg.id,
            transcript=analysis_output.transcript,
            facial_emotions=analysis_output.facial_emotions,
            voice_features=analysis_output.voice_features,
            text_analysis=analysis_output.text_analysis,
            model_version=settings.FUSION_MODEL_VERSION,
        )
        db.add(analysis_row)
        await db.flush()
        await db.refresh(analysis_row)

    user_msg.ai_analysis = analysis_row

    ai_msg = ChatMessage(
        session_id=session_id,
        sender_type=SenderType.AI,
        content=ai_content,
        input_mode=InputMode.TEXT,
    )
    ai_msg.ai_analysis = None
    db.add(ai_msg)
    await db.flush()

    return user_msg, ai_msg


#  service functions 

async def create_session(db: AsyncSession, user_id: UUID) -> ChatSession:
    session = ChatSession(user_id=user_id)
    db.add(session)
    await db.flush()
    return session


async def list_sessions(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ChatSession], int]:
    offset = (page - 1) * page_size
    total_result = await db.execute(
        select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user_id)
    )
    total: int = total_result.scalar_one()
    data_result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.started_at.desc())
        .offset(offset).limit(page_size)
    )
    return list(data_result.scalars().all()), total


async def get_session_messages(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    limit: int = 20,
    cursor: datetime | None = None,
) -> tuple[list[ChatMessage], datetime | None]:
    await _require_session(db, session_id, user_id)
    query = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .options(selectinload(ChatMessage.ai_analysis))
        .order_by(ChatMessage.created_at.desc())
        .limit(limit + 1)
    )
    if cursor:
        query = query.where(ChatMessage.created_at < cursor)
    result = await db.execute(query)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    messages = list(reversed(rows[:limit]))
    next_cursor: datetime | None = None
    if has_more and messages:
        next_cursor = messages[0].created_at
    return messages, next_cursor


async def send_text_message(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    content: str,
) -> ChatMessagePair:
    await _require_session(db, session_id, user_id)

    used_fallback   = False
    new_points      = 0
    emotion_label   = "neutral"
    bert_result_obj: TextAnalysisResult | None = None
    analysis_output: MediaAnalysisOutput | None = None

    try:
        bert_result_obj = await bert_classifier.classify_text(content)
        emotion_label = bert_result_obj.label
        if bert_result_obj.is_crisis:
            new_points += _RISK_PTS_CRISIS_CHAT
        elif bert_result_obj.is_deep_hopelessness:
            new_points += _RISK_PTS_HOPELESSNESS
        analysis_output = MediaAnalysisOutput(
            transcript=content,
            bert_result=bert_result_obj,
            text_analysis=_build_text_analysis_dict(bert_result_obj),
            facial_emotions=None,
            voice_features=None,
        )
    except Exception:
        used_fallback = True
        analysis_output = None

    message_points, risk_level, override_applied = _apply_safety_override(bert_result_obj, new_points)

    if override_applied:
        trigger_source = "Chat Text — Suicidal Intent (Safety Override)"
    elif new_points >= _RISK_PTS_CRISIS_CHAT:
        trigger_source = "Chat Text — Crisis Intent (BERT)"
    else:
        trigger_source = "Chat Text — Hopelessness (BERT)"

    if new_points > 0 or override_applied:
        await _log_risk(db, user_id, risk_level, trigger_source=trigger_source, total_points=message_points)

    ai_content = _pick_ai_response(risk_level, emotion_label, used_fallback, content)
    user_msg, ai_msg = await _persist_message_pair(
        db, session_id,
        user_content=content,
        input_mode=InputMode.TEXT,
        ai_content=ai_content,
        analysis_output=analysis_output,
    )
    return ChatMessagePair(user_message=user_msg, ai_message=ai_msg, risk_level=risk_level, used_fallback=used_fallback)


async def send_media_message(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    file_bytes: bytes,
    content_type: str,
) -> ChatMessagePair:
    # FIX: normalise mobile MIME types before validation
    # expo-av Android sends audio/3gp or audio/x-m4a — not in ALLOWED_MIME_TYPES
    content_type = _normalise_content_type(content_type)

    # Determine extension for the temp filename (media_processor needs it)
    ext_map = {
        "video/mp4":   "mp4",
        "audio/mpeg":  "mp3",
        "audio/wav":   "wav",
    }
    ext = ext_map.get(content_type, "mp4")
    filename = f"upload_{user_id}.{ext}"

    media_processor.validate_upload(
        filename=filename,
        content_type=content_type,
        size_bytes=len(file_bytes),
    )

    await _require_session(db, session_id, user_id)

    used_fallback   = False
    new_points      = 0
    emotion_label   = "neutral"
    bert_result_obj: TextAnalysisResult | None = None
    analysis_output: MediaAnalysisOutput | None = None
    user_content    = "[Media message]"

    try:
        # FIX: pass filename as 2nd arg — new process_media signature is
        # process_media(file_bytes, filename, content_type)
        analysis_output = await media_processor.process_media(
            file_bytes, filename, content_type
        )

        if analysis_output.transcript:
            user_content = analysis_output.transcript

        if analysis_output.bert_result:
            bert_result_obj = analysis_output.bert_result
            emotion_label = bert_result_obj.label
            if bert_result_obj.is_crisis:
                new_points += _RISK_PTS_CRISIS_CHAT
            elif bert_result_obj.is_deep_hopelessness:
                new_points += _RISK_PTS_HOPELESSNESS

        if check_physiological_distress(analysis_output):
            new_points += _RISK_PTS_PHYSIOLOGICAL

    except MediaProcessingError:
        used_fallback = True
        analysis_output = None
    except Exception as e:
        # FIX: logger is now defined at top of file
        logger.error(f"MEDIA PROCESSOR CRASHED: {e}", exc_info=True)
        used_fallback = True
        analysis_output = None

    message_points, risk_level, override_applied = _apply_safety_override(bert_result_obj, new_points)

    if new_points > 0 or override_applied:
        await _log_risk(
            db, user_id, risk_level,
            trigger_source="Media Message (Whisper + Wav2Vec2/DeepFace/Librosa)",
            total_points=message_points,
        )

    input_mode = InputMode.VIDEO if content_type == "video/mp4" else InputMode.VOICE
    ai_content = _pick_ai_response(risk_level, emotion_label, used_fallback, user_content)

    user_msg, ai_msg = await _persist_message_pair(
        db, session_id,
        user_content=user_content,
        input_mode=input_mode,
        ai_content=ai_content,
        analysis_output=analysis_output,
    )
    return ChatMessagePair(user_message=user_msg, ai_message=ai_msg, risk_level=risk_level, used_fallback=used_fallback)