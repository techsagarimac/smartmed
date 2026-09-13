"""Scan a package image and compare it with a saved medicine record."""

from __future__ import annotations

from datetime import date

from app.models import Medicine
from app.ocr.extract import ExtractedLabel
from app.ocr.pipeline import OCRResult, run_ocr_pipeline
from app.schemas import DetectedMedicine, ScheduledMedicineInfo, VerificationResponse
from app.services.analytics import is_expired
from app.services.matching import MatchInput, compare_label


def verify_scan(
    medicine: Medicine,
    image_bytes: bytes | None = None,
    barcode_hint: str | None = None,
    ocr_result: OCRResult | None = None,
) -> VerificationResponse:
    if ocr_result is None:
        if not image_bytes and not barcode_hint:
            raise ValueError("Upload a package photo or provide a barcode value.")
        if image_bytes:
            ocr_result = run_ocr_pipeline(image_bytes)
        else:
            extracted = ExtractedLabel(name=None, strength=None, barcode=barcode_hint, raw_text="")
            ocr_result = OCRResult(extracted=extracted, confidence=None, barcodes=[{"type": "HINT", "data": barcode_hint or ""}])

    extracted = ocr_result.extracted
    if barcode_hint and not extracted.barcode:
        extracted.barcode = barcode_hint.strip() or extracted.barcode

    matched = compare_label(
        MatchInput(name=medicine.name, strength=medicine.strength, barcode=medicine.barcode),
        extracted,
        ocr_result.confidence,
    )
    expired = is_expired(medicine)
    expiry_note = ""
    if expired:
        expiry_note = (
            " The expiry date saved for this medicine is in the past. Check the package "
            "and consult a pharmacist or healthcare professional."
        )
    elif medicine.expiry_date and medicine.expiry_date <= date.today():
        expiry_note = " Check the expiry date printed on the package."

    detected = DetectedMedicine(
        name=extracted.name,
        strength=extracted.strength,
        barcode=extracted.barcode,
        raw_text=extracted.raw_text,
        ocr_confidence=ocr_result.confidence,
    )
    return VerificationResponse(
        result=matched.result,
        headline=matched.headline,
        scheduled_medicine=ScheduledMedicineInfo(
            id=medicine.id,
            name=medicine.name,
            strength=medicine.strength,
            barcode=medicine.barcode,
            expiry_date=medicine.expiry_date,
            instructions=medicine.instructions,
        ),
        detected=detected,
        confidence=matched.confidence,
        name_similarity=round(matched.name_similarity, 3),
        barcode_matched=matched.barcode_matched,
        expired=expired,
        can_record_dose=matched.can_record_dose,
        disclaimer=matched.disclaimer,
        guidance=matched.guidance + expiry_note,
        error=None if matched.result != "no_text" else "No readable medicine text or barcode was found.",
    )
