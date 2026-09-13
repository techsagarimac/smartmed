"""Compare OCR/barcode output with a medicine the user already saved.

This is a label-matching helper. It does not decide whether a medicine is
clinically correct, authentic, or safe to take.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.config import get_settings
from app.ocr.extract import ExtractedLabel

DISCLAIMER = (
    "SmartMed only compares scanned package text with medicines you have already "
    "saved. It does not diagnose conditions, prescribe medicines, recommend dosages, "
    "or confirm that a medicine is medically safe to take."
)

GUIDANCE_UNCERTAIN = (
    "If you are uncertain, check the package and your prescription, or contact a "
    "pharmacist or healthcare professional. Do not take or skip a medicine based "
    "only on this scan result."
)

PACKAGING_WORDS = {
    "tablet",
    "tablets",
    "capsule",
    "capsules",
    "syrup",
    "mg",
    "ml",
    "mcg",
    "iu",
}


@dataclass
class MatchInput:
    name: str
    strength: str = ""
    barcode: str | None = None


@dataclass
class MatchResult:
    result: str
    headline: str
    confidence: float | None
    name_similarity: float
    barcode_matched: bool | None
    can_record_dose: bool
    guidance: str = GUIDANCE_UNCERTAIN
    disclaimer: str = DISCLAIMER


def normalize_name(value: str | None) -> str:
    text = (value or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [token for token in text.split() if token and token not in PACKAGING_WORDS]
    return " ".join(tokens)


def normalize_barcode(value: str | None) -> str:
    return re.sub(r"\s+", "", (value or "").strip())


def normalize_strength(value: str | None) -> str:
    text = (value or "").lower().replace("microgram", "mcg").replace("i.u.", "iu")
    text = text.replace("milligram", "mg")
    text = re.sub(r"\s+", "", text)
    return text


def name_similarity(expected: str, detected: str) -> float:
    left = normalize_name(expected)
    right = normalize_name(detected)
    if not left or not right:
        return 0.0
    ratio = SequenceMatcher(None, left, right).ratio()
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if left_tokens and right_tokens:
        overlap = len(left_tokens & right_tokens) / len(left_tokens)
        return max(ratio, overlap)
    return ratio


def strengths_compatible(expected: str, detected: str | None) -> bool:
    left = normalize_strength(expected)
    right = normalize_strength(detected)
    if not left or not right:
        return False
    return left == right or left in right or right in left


def compare_label(expected: MatchInput, detected: ExtractedLabel, ocr_confidence: float | None) -> MatchResult:
    settings = get_settings()
    similarity = name_similarity(expected.name, detected.name or detected.raw_text)
    expected_barcode = normalize_barcode(expected.barcode)
    detected_barcode = normalize_barcode(detected.barcode)
    barcode_matched: bool | None = None
    if expected_barcode and detected_barcode:
        barcode_matched = expected_barcode == detected_barcode
    elif expected_barcode or detected_barcode:
        barcode_matched = None

    has_signal = bool(detected.name or detected.barcode or (detected.raw_text and len(detected.raw_text.strip()) >= 4))
    if not has_signal:
        return MatchResult(
            result="no_text",
            headline="No medicine text detected",
            confidence=_combine_confidence(ocr_confidence, 0.0),
            name_similarity=similarity,
            barcode_matched=barcode_matched,
            can_record_dose=False,
        )

    if barcode_matched is True:
        return MatchResult(
            result="match",
            headline="Medicine appears to match",
            confidence=_combine_confidence(ocr_confidence, 0.96),
            name_similarity=similarity,
            barcode_matched=True,
            can_record_dose=True,
        )

    if barcode_matched is False:
        return MatchResult(
            result="mismatch",
            headline="Medicine does not appear to match",
            confidence=_combine_confidence(ocr_confidence, 0.2),
            name_similarity=similarity,
            barcode_matched=False,
            can_record_dose=False,
        )

    strength_ok = strengths_compatible(expected.strength, detected.strength)
    matched = similarity >= settings.match_name_threshold or (
        similarity >= settings.match_name_with_strength_threshold and strength_ok
    )

    low_ocr = ocr_confidence is not None and ocr_confidence < settings.ocr_min_confidence
    if matched and low_ocr:
        return MatchResult(
            result="low_confidence",
            headline="Scan confidence is low",
            confidence=_combine_confidence(ocr_confidence, similarity),
            name_similarity=similarity,
            barcode_matched=barcode_matched,
            can_record_dose=False,
        )

    if matched:
        return MatchResult(
            result="match",
            headline="Medicine appears to match",
            confidence=_combine_confidence(ocr_confidence, similarity),
            name_similarity=similarity,
            barcode_matched=barcode_matched,
            can_record_dose=True,
        )

    if low_ocr and similarity < settings.match_name_with_strength_threshold:
        return MatchResult(
            result="low_confidence",
            headline="Scan confidence is low",
            confidence=_combine_confidence(ocr_confidence, similarity),
            name_similarity=similarity,
            barcode_matched=barcode_matched,
            can_record_dose=False,
        )

    return MatchResult(
        result="mismatch",
        headline="Medicine does not appear to match",
        confidence=_combine_confidence(ocr_confidence, similarity),
        name_similarity=similarity,
        barcode_matched=barcode_matched,
        can_record_dose=False,
    )


def _combine_confidence(ocr_confidence: float | None, similarity: float) -> float:
    if ocr_confidence is None:
        return round(max(0.0, min(similarity, 1.0)), 3)
    ocr_ratio = max(0.0, min(ocr_confidence / 100.0, 1.0))
    return round((ocr_ratio * 0.45) + (max(0.0, min(similarity, 1.0)) * 0.55), 3)
