from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from models.journal import JournalEntry
from schemas.journal import JournalCreate, JournalResponse


router = APIRouter(prefix="/journals", tags=["Journal"])


def _stub_sentiment(text: str) -> str:
    """Stub — replace with DistilRoBERTa inference."""
    positive = ["happy", "great", "good", "love", "wonderful", "excited"]
    negative = ["sad", "anxious", "depressed", "hopeless", "tired", "overwhelmed"]
    lower = text.lower()
    pos = sum(1 for w in positive if w in lower)
    neg = sum(1 for w in negative if w in lower)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Neutral"


@router.post("/", response_model=JournalResponse, status_code=201)
def create_entry(
    payload: JournalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entry = JournalEntry(
        user_id=current_user.user_id,
        title=payload.title,
        content=payload.content,
        sentiment=_stub_sentiment(payload.content),
        prompt_used=payload.prompt_used,
        entry_date=payload.entry_date or date.today(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=List[JournalResponse])
def list_entries(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == current_user.user_id)
        .order_by(JournalEntry.entry_date.desc())
        .limit(limit)
        .all()
    )


@router.get("/{entry_id}", response_model=JournalResponse)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.entry_id == entry_id,
        JournalEntry.user_id == current_user.user_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.entry_id == entry_id,
        JournalEntry.user_id == current_user.user_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()