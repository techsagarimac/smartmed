"""Medicine CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.models import Medicine, Schedule, User
from app.schemas import MedicineCreate, MedicineOut, MedicineUpdate, MessageResponse
from app.services.auth import get_current_user
from app.services.medicines import get_owned_medicine, medicine_payload

router = APIRouter(prefix="/medicines", tags=["medicines"])


@router.get("", response_model=list[MedicineOut])
def list_medicines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    medicines = (
        db.query(Medicine)
        .options(selectinload(Medicine.schedules))
        .filter(Medicine.user_id == current_user.id)
        .order_by(Medicine.name.asc())
        .all()
    )
    return [medicine_payload(item) for item in medicines]


@router.post("", response_model=MedicineOut, status_code=status.HTTP_201_CREATED)
def create_medicine(
    payload: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medicine = Medicine(
        user_id=current_user.id,
        name=payload.name,
        strength=payload.strength.strip(),
        instructions=payload.instructions.strip(),
        expiry_date=payload.expiry_date,
        barcode=payload.barcode,
    )
    db.add(medicine)
    db.flush()
    for schedule in payload.schedules:
        db.add(
            Schedule(
                medicine_id=medicine.id,
                time=schedule.time,
                frequency=schedule.frequency,
                start_date=schedule.start_date,
                end_date=schedule.end_date,
            )
        )
    db.commit()
    db.refresh(medicine)
    return medicine_payload(get_owned_medicine(db, current_user, medicine.id))


@router.get("/{medicine_id}", response_model=MedicineOut)
def get_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return medicine_payload(get_owned_medicine(db, current_user, medicine_id))


@router.put("/{medicine_id}", response_model=MedicineOut)
def update_medicine(
    medicine_id: int,
    payload: MedicineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medicine = get_owned_medicine(db, current_user, medicine_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        name = data["name"].strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Medicine name is required.")
        medicine.name = name
    if "strength" in data and data["strength"] is not None:
        medicine.strength = data["strength"].strip()
    if "instructions" in data and data["instructions"] is not None:
        medicine.instructions = data["instructions"].strip()
    if "expiry_date" in data:
        medicine.expiry_date = data["expiry_date"]
    if "barcode" in data:
        barcode = data["barcode"]
        medicine.barcode = barcode.strip() if isinstance(barcode, str) and barcode.strip() else None
    db.commit()
    db.refresh(medicine)
    return medicine_payload(medicine)


@router.delete("/{medicine_id}", response_model=MessageResponse)
def delete_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medicine = get_owned_medicine(db, current_user, medicine_id)
    db.delete(medicine)
    db.commit()
    return MessageResponse(detail="Medicine deleted.")
