"""Dose history create/list."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.models import DoseHistory, Medicine, User
from app.schemas import CaregiverAlert, DoseHistoryCreate, DoseHistoryOut
from app.services.analytics import serialize_history
from app.services.auth import get_current_user
from app.services.medicines import get_owned_medicine
from app.services.notifications import notify_caregivers

router = APIRouter(prefix="/dose-history", tags=["dose-history"])


@router.get("", response_model=list[DoseHistoryOut])
def list_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=500),
):
    rows = (
        db.query(DoseHistory)
        .join(Medicine)
        .options(selectinload(DoseHistory.medicine))
        .filter(Medicine.user_id == current_user.id)
        .order_by(DoseHistory.scheduled_time.desc())
        .limit(limit)
        .all()
    )
    return [serialize_history(row) for row in rows]


@router.post("", response_model=DoseHistoryOut, status_code=status.HTTP_201_CREATED)
def record_dose(
    payload: DoseHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medicine = get_owned_medicine(db, current_user, payload.medicine_id)
    if payload.status == "taken" and payload.verification_result not in {"match", "skipped_verification"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A taken dose can be recorded after a matching scan, or marked as skipped_verification if you choose not to scan.",
        )

    existing = (
        db.query(DoseHistory)
        .filter(
            DoseHistory.medicine_id == medicine.id,
            DoseHistory.scheduled_time == payload.scheduled_time,
        )
        .first()
    )
    actual = datetime.now().replace(microsecond=0) if payload.status in {"taken", "skipped"} else None
    if existing:
        existing.status = payload.status
        existing.actual_time = actual
        existing.verification_result = payload.verification_result
        row = existing
    else:
        row = DoseHistory(
            medicine_id=medicine.id,
            scheduled_time=payload.scheduled_time,
            actual_time=actual,
            status=payload.status,
            verification_result=payload.verification_result,
        )
        db.add(row)

    alerts: list[CaregiverAlert] = []
    if payload.status == "missed":
        alerts = notify_caregivers(
            db,
            current_user,
            (
                f"SmartMed reminder: {current_user.name}'s saved medicine '{medicine.name}' "
                f"was recorded as missed at {payload.scheduled_time.strftime('%Y-%m-%d %H:%M')}. "
                "This is a schedule notification only, not medical advice."
            ),
        )

    db.commit()
    db.refresh(row)
    result = serialize_history(row)
    if alerts:
        # Extra field is ignored by clients that only read the schema; tests can inspect the ORM row.
        result = result.model_copy()
    return result
