from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from models.chat import ChatSession, ChatMessage
from schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatSessionResponse

router = APIRouter(prefix="/chat", tags=["Chatbot"])


def _get_or_create_session(session_id, user_id, db) -> ChatSession:
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    session = ChatSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _generate_bot_reply(user_text: str) -> dict:
    """
    Stub — replace with DistilRoBERTa + CBT logic.
    Returns: { content, text_emotion, crisis_flag }
    """
    crisis_keywords = ["suicide", "kill myself", "end my life", "can't go on"]
    crisis = any(kw in user_text.lower() for kw in crisis_keywords)

    if crisis:
        return {
            "content": (
                "I hear you, and I'm really glad you reached out. "
                "Please contact a crisis helpline immediately — "
                "Nepal: 1166 | International: befrienders.org. "
                "You are not alone."
            ),
            "text_emotion": "distress",
            "crisis_flag": True,
        }

    return {
        "content": "Thank you for sharing. Can you tell me more about how you've been feeling today?",
        "text_emotion": "neutral",
        "crisis_flag": False,
    }


# POST /chat/message 
@router.post("/message", response_model=List[ChatMessageResponse], status_code=201)
def send_message(
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session = _get_or_create_session(payload.session_id, current_user.user_id, db)

    # Save user message
    user_msg = ChatMessage(
        session_id=session.session_id,
        user_id=current_user.user_id,
        role="user",
        content=payload.content,
    )
    db.add(user_msg)

    # Generate and save bot reply
    reply_data = _generate_bot_reply(payload.content)
    bot_msg = ChatMessage(
        session_id=session.session_id,
        user_id=current_user.user_id,
        role="assistant",
        **reply_data,
    )
    db.add(bot_msg)

    # Update session counters
    session.message_count += 2
    if reply_data["crisis_flag"]:
        session.risk_flag = True

    db.commit()
    db.refresh(user_msg)
    db.refresh(bot_msg)

    return [user_msg, bot_msg]


# GET /chat/sessions 
@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.user_id)
        .order_by(ChatSession.started_at.desc())
        .limit(20)
        .all()
    )


# GET /chat/sessions/{session_id}/messages 
@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )