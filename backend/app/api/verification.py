"""POST /verification/scan — compare a package photo or barcode with a saved medicine."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import get_db
from app.models import User
from app.ocr.pipeline import OCRFailedError, OCRUnavailableError
from app.schemas import VerificationResponse
from app.services.auth import get_current_user
from app.services.medicines import get_owned_medicine
from app.services.verification import verify_scan

router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/scan", response_model=VerificationResponse)
async def scan_medicine(
    medicine_id: int = Form(...),
    barcode: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    medicine = get_owned_medicine(db, current_user, medicine_id)
    settings = get_settings()
    image_bytes: bytes | None = None
    if file is not None and file.filename:
        image_bytes = await file.read()
        max_bytes = settings.max_image_mb * 1024 * 1024
        if len(image_bytes) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Image is too large. Maximum size is {settings.max_image_mb} MB.",
            )
        if not image_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded image was empty.")

    barcode_hint = (barcode or "").strip() or None
    if image_bytes is None and barcode_hint is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Capture or upload a package photo, or provide a barcode.",
        )

    try:
        return verify_scan(medicine, image_bytes=image_bytes, barcode_hint=barcode_hint)
    except OCRUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except OCRFailedError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
