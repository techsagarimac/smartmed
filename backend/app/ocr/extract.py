"""Turn noisy OCR text into a possible medicine name and strength.

This is string cleanup only. It does not look up drugs or suggest treatment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PACKAGING_WORDS = {
    "tablet",
    "tablets",
    "tab",
    "tabs",
    "capsule",
    "capsules",
    "cap",
    "caps",
    "syrup",
    "injection",
    "strip",
    "pack",
    "batch",
    "mfg",
    "exp",
    "expiry",
    "best",
    "before",
    "composition",
    "each",
    "contains",
    "dose",
    "dosage",
    "ip",
    "usp",
    "bp",
    "rx",
    "nrx",
    "keep",
    "reach",
    "children",
    "storage",
    "store",
    "protect",
    "light",
    "moisture",
    "manufactured",
    "marketed",
    "limited",
    "ltd",
    "pvt",
    "private",
}

STRENGTH_RE = re.compile(
    r"(\d+[\.,]?\d*)\s*(mg|mcg|ug|g|ml|iu|i\.u\.|%)",
    re.IGNORECASE,
)
BARCODE_RE = re.compile(r"\b(\d{8,14})\b")
LETTER_RE = re.compile(r"[A-Za-z]")


@dataclass
class ExtractedLabel:
    name: str | None
    strength: str | None
    barcode: str | None
    raw_text: str
    lines: list[str] = field(default_factory=list)


def cleanup_ocr_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("\x0c", " ")
    cleaned = re.sub(r"[|•·]+", " ", cleaned)
    cleaned = re.sub(r"[^\S\n]+", " ", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    return cleaned.strip()


def _line_score(line: str) -> float:
    letters = len(LETTER_RE.findall(line))
    digits = sum(ch.isdigit() for ch in line)
    if letters < 3:
        return 0.0
    words = [w for w in re.split(r"\s+", line.lower()) if w]
    packaging_hits = sum(1 for w in words if w.strip(".,()") in PACKAGING_WORDS)
    score = letters - digits * 0.4 - packaging_hits * 4
    if STRENGTH_RE.search(line):
        score += 2
    if 4 <= letters <= 40:
        score += 3
    return score


def extract_strength(text: str) -> str | None:
    match = STRENGTH_RE.search(text or "")
    if not match:
        return None
    amount = match.group(1).replace(",", ".")
    unit = match.group(2).lower().replace(".", "")
    if unit == "ug":
        unit = "mcg"
    if unit == "iu":
        unit = "IU"
    else:
        unit = unit.lower()
    return f"{amount} {unit}"


def extract_barcode_from_text(text: str) -> str | None:
    matches = BARCODE_RE.findall(text or "")
    if not matches:
        return None
    return max(matches, key=len)


def extract_medicine_name(text: str) -> str | None:
    cleaned = cleanup_ocr_text(text)
    if not cleaned:
        return None
    best_line = ""
    best_score = 0.0
    for raw_line in cleaned.splitlines():
        line = raw_line.strip(" -:\t")
        if not line:
            continue
        score = _line_score(line)
        if score > best_score:
            best_score = score
            best_line = line
    if best_score < 4 or not best_line:
        compact = re.sub(r"\s+", " ", cleaned)
        tokens = []
        for token in compact.split(" "):
            lower = token.lower().strip(".,()")
            if lower in PACKAGING_WORDS or STRENGTH_RE.fullmatch(token):
                continue
            if LETTER_RE.search(token):
                tokens.append(token)
            if len(tokens) >= 4:
                break
        candidate = " ".join(tokens).strip()
        return candidate or None
    name = STRENGTH_RE.sub("", best_line)
    name = re.sub(r"\s+", " ", name).strip(" -")
    return name or None


def extract_label(text: str) -> ExtractedLabel:
    cleaned = cleanup_ocr_text(text)
    return ExtractedLabel(
        name=extract_medicine_name(cleaned),
        strength=extract_strength(cleaned),
        barcode=extract_barcode_from_text(cleaned),
        raw_text=cleaned,
        lines=[line.strip() for line in cleaned.splitlines() if line.strip()],
    )
