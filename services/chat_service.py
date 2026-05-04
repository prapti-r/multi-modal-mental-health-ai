"""
services/chat_service.py
────────────────────────
Chat engine business logic — the core of Eunoia's real-time support.

Responsibilities:
  1. Session management  — create, list, ownership checks.
  2. Text message flow   — BERT classify → pick CBT response → risk evaluate.
  3. Media message flow  — validate upload → process_media → BERT → risk → store.
  4. Risk evaluation     — per-message points logged for weekly fusion; immediate
                           response level based on THIS message only.
  5. Fallback mode       — if ML pipeline fails, revert to CBT templates (PRD §5).
  6. Cursor-based pagination — for GET /chat/sessions/{id}/messages.

PRD §7.1 risk point sources handled here:
    • BERT detects Crisis/Self-Harm in chat text        → 40 pts
    • BERT detects Deep Hopelessness in chat text       → 20 pts
    • Physiological cues (facial/voice) > 85%           → 20 pts
    (Journal "Deep Hopelessness"  → journal_service)
    (PHQ-9/GAD-7 ≥ 15             → assessment_service)

Risk design (per-message, not daily cumulative):
    Each message is scored independently. The risk_level returned to the client
    reflects ONLY this message's contribution. This prevents a single severe
    message from locking all subsequent messages into crisis mode.

    The risk_log rows are still written per message so the weekly Late Fusion
    model can sum them for MHI calculation — that aggregation is unaffected.

    Example:
        09:00 — "I feel sad and tired"        → hopeless=0.43 → 20 pts → Mild
        09:05 — "I don't want to live"        → suicidal=0.45 → 40 pts → SEVERE (safety override)
        09:10 — "Today was okay"              → positive=0.92 →  0 pts → Mild ✓ (no longer stuck)

Safety override (clinical requirement beyond PRD):
    If BERT classifies text as suicidal with score ≥ SAFETY_OVERRIDE_THRESHOLD,
    we force SEVERE regardless of this message's point contribution. Explicit
    suicidal statements must ALWAYS trigger immediate crisis intervention.
    This is a clinical safety floor, not a protocol deviation.
"""

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


# ── Risk point constants (PRD §7.1) ───────────────────────────────────────────

_RISK_PTS_CRISIS_CHAT   = 40   # BERT detects crisis/self-harm intent
_RISK_PTS_HOPELESSNESS  = 20   # BERT detects deep hopelessness
_RISK_PTS_PHYSIOLOGICAL = 20   # Facial/voice distress > 85%

# Safety override: if suicidal score clears this threshold, force SEVERE
# regardless of this message's point total. Explicit suicidal statements must
# always trigger immediate crisis response (clinical safety requirement).
_SAFETY_OVERRIDE_THRESHOLD = 0.40


# ── Output dataclass ───────────────────────────────────────────────────────────

@dataclass
class ChatMessagePair:
    user_message:  ChatMessage
    ai_message:    ChatMessage
    risk_level:    RiskLevel
    used_fallback: bool


# ── Internal helpers ───────────────────────────────────────────────────────────

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
    """Classify per-message points into a risk tier (PRD §7.1)."""
    if points >= settings.RISK_SEVERE_THRESHOLD:    # ≥ 60
        return RiskLevel.SEVERE
    if points >= settings.RISK_MODERATE_THRESHOLD:  # ≥ 31
        return RiskLevel.MODERATE
    return RiskLevel.MILD


def _apply_safety_override(
    bert_result: TextAnalysisResult | None,
    message_points: int,
) -> tuple[int, RiskLevel, bool]:
    """
    Clinical safety override: explicit suicidal statements always trigger SEVERE.

    A single message with suicidal score ≥ 0.40 must trigger immediate crisis
    intervention regardless of point total. We force points to RISK_SEVERE_THRESHOLD.

    Returns:
        (effective_points, risk_level, override_applied)
    """
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
    """
    Persist a risk_log row for this message's contribution.
    The weekly fusion model sums these rows for MHI calculation.
    """
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
    """
    Select the appropriate AI response based on risk level and emotion.

    Priority:
      1. SEVERE   → crisis response (always, regardless of emotion or fallback)
      2. MODERATE → de-escalation response
      3. Fallback mode → keyword-heuristic CBT template
      4. Normal   → emotion-matched CBT template (with greeting/empty detection)
    """
    if risk_level == RiskLevel.SEVERE:
        return get_crisis_response()
    if risk_level == RiskLevel.MODERATE:
        return get_moderate_risk_response()
    if used_fallback:
        return get_fallback_response(user_content)
    return get_cbt_response(emotion_label, user_text=user_content)


def _build_text_analysis_dict(bert_result: TextAnalysisResult) -> dict:
    """
    Build a JSONB-safe dict from a TextAnalysisResult.

    Explicit manual dict (not dataclasses.asdict) so the schema is stable
    and matches the dict produced in media_processor.py exactly.
    """
    return {
        "label":                bert_result.label,
        "score":                bert_result.score,
        "raw_label":            bert_result.raw_label,
        "is_crisis":            bert_result.is_crisis,
        "is_deep_hopelessness": bert_result.is_deep_hopelessness,
        "all_scores":           bert_result.all_scores,
    }


async def _persist_message_pair(
    db: AsyncSession,
    session_id: UUID,
    user_content: str,
    input_mode: InputMode,
    ai_content: str,
    analysis_output: MediaAnalysisOutput | None = None,
) -> tuple[ChatMessage, ChatMessage]:
    """
    Persist user message, optional AiAnalysisResult, and AI reply atomically.

    The ai_analysis relationship is set explicitly on the ORM object so that
    the immediately-returned ChatMessage has analysis data attached in-memory,
    avoiding the lazy-load failure that causes "ai_analysis: null" in the
    immediate POST response.
    """
    # User message
    user_msg = ChatMessage(
        session_id=session_id,
        sender_type=SenderType.USER,
        content=user_content,
        input_mode=input_mode,
    )
    db.add(user_msg)
    await db.flush()   # populate user_msg.id before FK reference

    # AI analysis result — written for both text and media messages
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
        await db.refresh(analysis_row)   # load server-defaults (id, timestamps)

    # Attach in-memory so Pydantic serialization works without a lazy load
    user_msg.ai_analysis = analysis_row

    # AI reply (always text)
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


# ── Public service functions ───────────────────────────────────────────────────

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
        select(func.count())
        .select_from(ChatSession)
        .where(ChatSession.user_id == user_id)
    )
    total: int = total_result.scalar_one()

    data_result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.started_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(data_result.scalars().all()), total


async def get_session_messages(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    limit: int = 20,
    cursor: datetime | None = None,
) -> tuple[list[ChatMessage], datetime | None]:
    """
    Cursor-based pagination for session message history.
    ai_analysis is eagerly loaded so serialization works in the route.
    """
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
        next_cursor = messages[0].created_at  # type: ignore[assignment]

    return messages, next_cursor


async def send_text_message(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    content: str,
) -> ChatMessagePair:
    """
    Process a plain-text user message.

    Flow:
        1. Verify session ownership.
        2. Run BERT classification.
        3. Determine this message's risk point contribution.
        4. Apply safety override if suicidal score ≥ threshold.
        5. Log risk event if points were generated.
        6. Pick CBT response; persist; return.

    Risk is per-message: prior messages in the day do NOT affect this response.
    The weekly fusion model aggregates all risk_log rows for MHI calculation.
    """
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

    # Per-message risk: only THIS message's contribution
    message_points, risk_level, override_applied = _apply_safety_override(
        bert_result_obj, new_points
    )

    if override_applied:
        trigger_source = "Chat Text — Suicidal Intent (Safety Override)"
    elif new_points >= _RISK_PTS_CRISIS_CHAT:
        trigger_source = "Chat Text — Crisis Intent (BERT)"
    else:
        trigger_source = "Chat Text — Hopelessness (BERT)"

    if new_points > 0 or override_applied:
        await _log_risk(
            db, user_id, risk_level,
            trigger_source=trigger_source,
            total_points=message_points,
        )

    ai_content = _pick_ai_response(risk_level, emotion_label, used_fallback, content)

    user_msg, ai_msg = await _persist_message_pair(
        db, session_id,
        user_content=content,
        input_mode=InputMode.TEXT,
        ai_content=ai_content,
        analysis_output=analysis_output,
    )

    return ChatMessagePair(
        user_message=user_msg,
        ai_message=ai_msg,
        risk_level=risk_level,
        used_fallback=used_fallback,
    )


async def send_media_message(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    file_bytes: bytes,
    content_type: str,
) -> ChatMessagePair:
    """
    Process a voice or video message.

    Flow:
        1. Validate upload (MIME type + size).
        2. Verify session ownership.
        3. Run media pipeline (Whisper → BERT → Librosa/Wav2Vec2/DeepFace).
        4. Determine this message's risk point contribution.
        5. Apply safety override if suicidal.
        6. Log, respond, persist.

    Raw bytes never persist beyond this call (PRD §5 retention rule).
    Risk is per-message — same policy as send_text_message.
    """
    media_processor.validate_upload(
        filename="upload",
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
        analysis_output = await media_processor.process_media(file_bytes, content_type)

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
        used_fallback   = True
        analysis_output = None
    except Exception:
        used_fallback   = True
        analysis_output = None

    # Per-message risk: only THIS message's contribution
    message_points, risk_level, override_applied = _apply_safety_override(
        bert_result_obj, new_points
    )

    if new_points > 0 or override_applied:
        await _log_risk(
            db, user_id, risk_level,
            trigger_source="Media Message (Whisper + Wav2Vec2/DeepFace/Librosa)",
            total_points=message_points,   # ← was cumulative_points (bug fixed)
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

    return ChatMessagePair(
        user_message=user_msg,
        ai_message=ai_msg,
        risk_level=risk_level,
        used_fallback=used_fallback,
    )