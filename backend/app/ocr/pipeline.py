"""Replaceable OCR + barcode pipeline.

Later this file can call a cloud vision model. Callers should depend on
`run_ocr_pipeline` rather than pytesseract directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np
import pytesseract

from app.config import get_settings
from app.ocr.extract import ExtractedLabel, extract_label
from app.ocr.preprocess import decode_image_bytes, preprocess_for_ocr, to_grayscale


class OCRUnavailableError(RuntimeError):
    pass


class OCRFailedError(RuntimeError):
    pass


@dataclass
class OCRResult:
    extracted: ExtractedLabel
    confidence: float | None
    barcodes: list[dict[str, str]] = field(default_factory=list)
    engine: str = "tesseract"


def configure_tesseract() -> None:
    settings = get_settings()
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def tesseract_available() -> bool:
    try:
        configure_tesseract()
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _mean_confidence(data: dict) -> float | None:
    confs = []
    for value in data.get("conf", []):
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number >= 0:
            confs.append(number)
    if not confs:
        return None
    return float(sum(confs) / len(confs))


def _ocr_numpy(image: np.ndarray) -> tuple[str, float | None]:
    config = "--oem 3 --psm 6"
    try:
        text = pytesseract.image_to_string(image, config=config)
        data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError(
            "Tesseract OCR is not installed. Install Tesseract and retry, or set TESSERACT_CMD."
        ) from exc
    except Exception as exc:
        raise OCRFailedError("OCR could not read this image. Try a clearer photo of the package label.") from exc
    return text or "", _mean_confidence(data)


def detect_barcodes(image_bgr: np.ndarray) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    gray = to_grayscale(image_bgr)

    detector = cv2.QRCodeDetector()
    value, _points, _straight = detector.detectAndDecode(gray)
    if value:
        found.append({"type": "QR", "data": value.strip()})

    try:
        from pyzbar.pyzbar import decode as zbar_decode
    except Exception:
        zbar_decode = None

    if zbar_decode is not None:
        try:
            for item in zbar_decode(image_bgr):
                data = item.data.decode("utf-8", errors="ignore").strip()
                if data:
                    found.append({"type": str(item.type), "data": data})
        except Exception:
            pass

    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in found:
        key = f"{item['type']}:{item['data']}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def run_ocr_pipeline(image_bytes: bytes) -> OCRResult:
    """Full pipeline used by verification: image bytes → extracted label fields."""
    if not tesseract_available():
        raise OCRUnavailableError(
            "Tesseract OCR is not installed. Install Tesseract and retry, or set TESSERACT_CMD."
        )

    image = decode_image_bytes(image_bytes)
    stages = preprocess_for_ocr(image)

    texts: list[str] = []
    confidences: list[float] = []
    for key in ("threshold", "denoise", "gray"):
        text, confidence = _ocr_numpy(stages[key])
        if text.strip():
            texts.append(text)
        if confidence is not None:
            confidences.append(confidence)

    combined = "\n".join(texts)
    if not combined.strip():
        # Last attempt on the colour resized image.
        text, confidence = _ocr_numpy(stages["resized"])
        combined = text
        if confidence is not None:
            confidences.append(confidence)

    extracted = extract_label(combined)
    barcodes = detect_barcodes(stages["resized"])
    if barcodes and not extracted.barcode:
        extracted.barcode = barcodes[0]["data"]

    confidence = max(confidences) if confidences else None
    return OCRResult(extracted=extracted, confidence=confidence, barcodes=barcodes)
