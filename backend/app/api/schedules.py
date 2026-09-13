"""Schedule CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Medicine, Schedule, User
from app.schemas import ScheduleCreate, ScheduleOut, ScheduleUpdate, MessageResponse
from app.services.auth import get_current_user
from app.services.medicines import get_owned_medicine, get_owned_schedule

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleOut])
def list_schedules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Schedule)
        .join(Medicine)
        .filter(Medicine.user_id == current_user.id)
        .order_by(Schedule.start_date.asc(), Schedule.time.asc())
        .all()
    )
    return rows


@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_medicine(db, current_user, payload.medicine_id)
    if payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="End date cannot be before the start date.")
    schedule = Schedule(
        medicine_id=payload.medicine_id,
        time=payload.time,
        frequency=payload.frequency,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = get_owned_schedule(db, current_user, schedule_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(schedule, field, value)
    start = schedule.start_date
    end = schedule.end_date
    if end and start and end < start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="End date cannot be before the start date.")
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", response_model=MessageResponse)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = get_owned_schedule(db, current_user, schedule_id)
    db.delete(schedule)
    db.commit()
    return MessageResponse(detail="Schedule deleted.")
