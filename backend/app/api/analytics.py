"""GET /analytics and GET /reminders."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import User
from app.schemas import AnalyticsResponse, ReminderItem
from app.services.analytics import build_analytics
from app.services.auth import get_current_user

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return build_analytics(db, current_user)


@router.get("/reminders", response_model=list[ReminderItem])
def reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return build_analytics(db, current_user).today_medicines
