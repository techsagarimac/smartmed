"""Medicine ownership helpers and expiry flags."""

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models import Medicine, Schedule, User
from app.services.analytics import is_expired, is_expiring_soon, serialize_medicine


def get_owned_medicine(db: Session, user: User, medicine_id: int) -> Medicine:
    medicine = (
        db.query(Medicine)
        .options(selectinload(Medicine.schedules))
        .filter(Medicine.id == medicine_id, Medicine.user_id == user.id)
        .first()
    )
    if not medicine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")
    return medicine


def get_owned_schedule(db: Session, user: User, schedule_id: int) -> Schedule:
    schedule = (
        db.query(Schedule)
        .join(Medicine)
        .filter(Schedule.id == schedule_id, Medicine.user_id == user.id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found.")
    return schedule


def medicine_payload(medicine: Medicine):
    return serialize_medicine(medicine)


def expiry_state(medicine: Medicine, on: date | None = None) -> dict[str, bool]:
    return {"expired": is_expired(medicine, on), "expiring_soon": is_expiring_soon(medicine, on)}
