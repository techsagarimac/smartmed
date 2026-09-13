from datetime import date

from app.ocr.extract import ExtractedLabel
from app.ocr.pipeline import OCRResult
from tests.conftest import auth_header, register


def test_scan_endpoint_with_mocked_ocr(client, monkeypatch):
    token = register(client)["access_token"]
    headers = auth_header(token)
    medicine = client.post(
        "/medicines",
        headers=headers,
        json={"name": "Paracetamol", "strength": "500 mg", "expiry_date": date.today().isoformat()},
    ).json()

    def fake_pipeline(_image_bytes):
        extracted = ExtractedLabel(
            name="Paracetamol",
            strength="500 mg",
            barcode=None,
            raw_text="PARACETAMOL 500 mg tablets",
        )
        return OCRResult(extracted=extracted, confidence=82.0, barcodes=[])

    monkeypatch.setattr("app.services.verification.run_ocr_pipeline", fake_pipeline)

    response = client.post(
        "/verification/scan",
        headers=headers,
        data={"medicine_id": str(medicine["id"])},
        files={"file": ("label.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["result"] == "match"
    assert body["can_record_dose"] is True
    assert "does not diagnose" in body["disclaimer"].lower() or "not diagnose" in body["disclaimer"].lower()


def test_barcode_only_mismatch(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    medicine = client.post(
        "/medicines",
        headers=headers,
        json={"name": "Metformin", "strength": "500 mg", "barcode": "8901234567890"},
    ).json()
    response = client.post(
        "/verification/scan",
        headers=headers,
        data={"medicine_id": str(medicine["id"]), "barcode": "0000000000000"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["result"] == "mismatch"
    assert response.json()["can_record_dose"] is False
