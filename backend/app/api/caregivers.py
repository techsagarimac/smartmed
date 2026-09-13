"""Optional caregiver contacts."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import get_db
from app.models import Caregiver, User
from app.schemas import CaregiverCreate, CaregiverOut, CaregiverUpdate, MessageResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/caregivers", tags=["caregivers"])


@router.get("", response_model=list[CaregiverOut])
def list_caregivers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Caregiver)
        .filter(Caregiver.user_id == current_user.id)
        .order_by(Caregiver.caregiver_name.asc())
        .all()
    )


@router.post("", response_model=CaregiverOut, status_code=status.HTTP_201_CREATED)
def create_caregiver(
    payload: CaregiverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregiver = Caregiver(
        user_id=current_user.id,
        caregiver_name=payload.caregiver_name.strip(),
        caregiver_contact=payload.caregiver_contact.strip(),
        notifications_enabled=payload.notifications_enabled,
    )
    db.add(caregiver)
    db.commit()
    db.refresh(caregiver)
    return caregiver


@router.put("/{caregiver_id}", response_model=CaregiverOut)
def update_caregiver(
    caregiver_id: int,
    payload: CaregiverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregiver = (
        db.query(Caregiver)
        .filter(Caregiver.id == caregiver_id, Caregiver.user_id == current_user.id)
        .first()
    )
    if not caregiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caregiver not found.")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(caregiver, field, value)
    db.commit()
    db.refresh(caregiver)
    return caregiver


@router.delete("/{caregiver_id}", response_model=MessageResponse)
def delete_caregiver(
    caregiver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    caregiver = (
        db.query(Caregiver)
        .filter(Caregiver.id == caregiver_id, Caregiver.user_id == current_user.id)
        .first()
    )
    if not caregiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caregiver not found.")
    db.delete(caregiver)
    db.commit()
    return MessageResponse(detail="Caregiver removed.")


@router.get("/status/delivery")
def delivery_status(current_user: User = Depends(get_current_user)):
    settings = get_settings()
    return {
        "smtp_configured": settings.smtp_configured,
        "detail": (
            "Missed-dose alerts can be emailed because SMTP is configured."
            if settings.smtp_configured
            else "SMTP is not configured. Missed-dose alerts are logged in the server output only."
        ),
    }
