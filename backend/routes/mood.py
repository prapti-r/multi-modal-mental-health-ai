from datetime import date
from typing import List

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from models.mood import MoodCheckin
from schemas.mood import MoodCheckinCreate, MoodCheckinResponse

router = APIRouter(prefix="/moods", tags=["Mood Tracking"])


#  POST /mood/ 
@router.post("/", response_model=MoodCheckinResponse, status_code=201)
def create_checkin(
    payload: MoodCheckinCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    checkin_date = payload.checkin_date or date.today()

    # One check-in per day per user
    existing = db.query(MoodCheckin).filter(
        MoodCheckin.user_id == current_user.user_id,
        MoodCheckin.checkin_date == checkin_date,
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Mood already logged for today")

    checkin = MoodCheckin(
        user_id=current_user.user_id,
        mood_score=payload.mood_score,
        mood_label=payload.mood_label,
        note=payload.note,
        checkin_date=checkin_date,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


#  GET /mood/ 
@router.get("/", response_model=List[MoodCheckinResponse])
def get_checkins(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == current_user.user_id)
        .order_by(MoodCheckin.checkin_date.desc())
        .limit(limit)
        .all()
    )


#  GET /mood/today 
@router.get("/today", response_model=MoodCheckinResponse)
def get_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    checkin = db.query(MoodCheckin).filter(
        MoodCheckin.user_id == current_user.user_id,
        MoodCheckin.checkin_date == date.today(),
    ).first()

    if not checkin:
        raise HTTPException(status_code=404, detail="No mood logged today yet")
    return checkin