from app.ocr.extract import extract_label
from app.ocr.extract import ExtractedLabel
from app.services.matching import MatchInput, compare_label


def test_extract_medicine_name_and_strength():
    text = "PARACETAMOL\n500 mg Tablets\nEach uncoated tablet contains Paracetamol IP 500 mg"
    extracted = extract_label(text)
    assert extracted.name is not None
    assert "paracetamol" in extracted.name.lower()
    assert extracted.strength is not None
    assert "500" in extracted.strength
    assert "mg" in extracted.strength.lower()


def test_match_by_name():
    result = compare_label(
        MatchInput(name="Paracetamol", strength="500 mg"),
        ExtractedLabel(name="Paracetamol", strength="500 mg", barcode=None, raw_text="PARACETAMOL 500 mg"),
        ocr_confidence=80,
    )
    assert result.result == "match"
    assert result.can_record_dose is True
    assert "appears to match" in result.headline


def test_mismatch_different_name():
    result = compare_label(
        MatchInput(name="Metformin", strength="500 mg"),
        ExtractedLabel(name="Ibuprofen", strength="400 mg", barcode=None, raw_text="IBUPROFEN 400 mg"),
        ocr_confidence=85,
    )
    assert result.result == "mismatch"
    assert result.can_record_dose is False


def test_barcode_match_overrides_name_noise():
    result = compare_label(
        MatchInput(name="Metformin", strength="500 mg", barcode="8901234567890"),
        ExtractedLabel(name="METF0RMIN", strength=None, barcode="8901234567890", raw_text="METF0RMIN"),
        ocr_confidence=70,
    )
    assert result.result == "match"
    assert result.barcode_matched is True


def test_barcode_mismatch():
    result = compare_label(
        MatchInput(name="Metformin", strength="500 mg", barcode="8901234567890"),
        ExtractedLabel(name="Metformin", strength="500 mg", barcode="1111111111111", raw_text="Metformin"),
        ocr_confidence=90,
    )
    assert result.result == "mismatch"
    assert result.barcode_matched is False


def test_no_text_detected():
    result = compare_label(
        MatchInput(name="Paracetamol"),
        ExtractedLabel(name=None, strength=None, barcode=None, raw_text=""),
        ocr_confidence=None,
    )
    assert result.result == "no_text"
    assert result.can_record_dose is False
