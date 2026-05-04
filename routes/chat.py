"""
routes/chat.py
──────────────
Chat engine endpoints — all authenticated.

Routes:
    POST  /chat/session                         Start a new session
    GET   /chat/sessions                        List all past sessions (paginated)
    POST  /chat/message                         Send a text message
    POST  /chat/message/media                   Send a voice or video message (multipart)
    GET   /chat/sessions/{session_id}/messages  Cursor-paginated message history

The media endpoint enforces PRD constraints:
    • Max 10 MB per upload
    • Allowed MIME types: video/mp4, audio/wav, audio/mpeg
    • Raw file bytes are passed in-memory to the ML pipeline and never persisted

The message response always includes `risk_level` so the client can navigate
to the Crisis screen immediately if `risk_level == "severe"` (PRD §3.2).
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.dependencies import get_current_user_id
from core.exceptions import ValidationError
from schemas.chat import (
    ChatMessageOut,
    ChatMessagePairOut,
    ChatSessionListOut,
    ChatSessionOut,
    MessageHistoryOut,
    TextMessageCreate,
)
from services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat Engine"])


# ── Session management ────────────────────────────────────────────────────────

@router.post(
    "/session",
    response_model=ChatSessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new chat session",
    description=(
        "Opens a new conversation thread and returns a session_id. "
        "Pass session_id in every subsequent message request."
    ),
)
async def create_session(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionOut:
    session = await chat_service.create_session(db, user_id)
    return ChatSessionOut.model_validate(session)


@router.get(
    "/sessions",
    response_model=ChatSessionListOut,
    summary="List all chat sessions",
    description="Returns paginated session summaries ordered newest-first.",
)
async def list_sessions(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
) -> ChatSessionListOut:
    sessions, total = await chat_service.list_sessions(db, user_id, page, page_size)
    return ChatSessionListOut(
        sessions=[ChatSessionOut.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Text message ──────────────────────────────────────────────────────────────

@router.post(
    "/message",
    response_model=ChatMessagePairOut,
    status_code=status.HTTP_201_CREATED,
    summary="Send a text message",
    description=(
        "Sends a text message, runs BERT sentiment classification, "
        "and returns an AI CBT response. "
        "Check `risk_level` in the response — if `severe`, navigate to the Crisis screen immediately."
    ),
)
async def send_text_message(
    payload: TextMessageCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ChatMessagePairOut:
    pair = await chat_service.send_text_message(
        db, user_id, payload.session_id, payload.content
    )
    return ChatMessagePairOut(
        user_message=ChatMessageOut.model_validate(pair.user_message),
        ai_message=ChatMessageOut.model_validate(pair.ai_message),
        risk_level=pair.risk_level,
        used_fallback=pair.used_fallback,
    )


# ── Media message ─────────────────────────────────────────────────────────────

@router.post(
    "/message/media",
    response_model=ChatMessagePairOut,
    status_code=status.HTTP_201_CREATED,
    summary="Send a voice or video check-in",
    description=(
        "Accepts a multipart/form-data upload (max 10 MB). "
        "Allowed types: `video/mp4`, `audio/wav`, `audio/mpeg`. "
        "The file is processed in-memory (Whisper → BERT → Librosa/DeepFace) "
        "and raw bytes are never stored to disk. "
        "On ML failure the system automatically falls back to CBT templates (PRD §5)."
    ),
)
async def send_media_message(
    session_id: UUID = Form(..., description="The active chat session ID."),
    file: UploadFile = File(..., description="Audio (.wav, .mp3) or video (.mp4) — max 10 MB."),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ChatMessagePairOut:
    # Read into memory — enforces PRD §5 in-memory only rule
    file_bytes = await file.read()
    content_type = file.content_type or ""

    # Fast path validation before hitting the service
    # try:
    #     from ml.media_processor import validate_upload
    #     validate_upload(file.filename or "upload", content_type, len(file_bytes))
    # except ValidationError as exc:
    #     raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.detail)

    pair = await chat_service.send_media_message(
        db, user_id, session_id, file_bytes, content_type
    )
    return ChatMessagePairOut(
        user_message=ChatMessageOut.model_validate(pair.user_message),
        ai_message=ChatMessageOut.model_validate(pair.ai_message),
        risk_level=pair.risk_level,
        used_fallback=pair.used_fallback,
    )


# ── Message history ───────────────────────────────────────────────────────────

@router.get(
    "/sessions/{session_id}/messages",
    response_model=MessageHistoryOut,
    summary="Get session message history",
    description=(
        "Cursor-based pagination — pass `?cursor=<ISO timestamp>` to fetch older messages. "
        "Messages are returned in chronological order (oldest first within the page). "
        "When `next_cursor` is null, there are no more messages to load."
    ),
)
async def get_session_messages(
    session_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=50, description="Messages per page."),
    cursor: datetime | None = Query(
        default=None,
        description="ISO 8601 timestamp — fetch messages older than this.",
    ),
) -> MessageHistoryOut:
    messages, next_cursor = await chat_service.get_session_messages(
        db, user_id, session_id, limit, cursor
    )
    return MessageHistoryOut(
        messages=[ChatMessageOut.model_validate(m) for m in messages],
        next_cursor=next_cursor,
        session_id=session_id,
    )