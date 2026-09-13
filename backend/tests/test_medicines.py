from datetime import date, timedelta

from tests.conftest import auth_header, register


def test_create_and_retrieve_medicine(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    expiry = (date.today() + timedelta(days=90)).isoformat()
    created = client.post(
        "/medicines",
        headers=headers,
        json={
            "name": "Paracetamol",
            "strength": "500 mg",
            "instructions": "After food",
            "expiry_date": expiry,
            "barcode": "8901234567890",
            "schedules": [
                {
                    "time": "08:00:00",
                    "frequency": "daily",
                    "start_date": date.today().isoformat(),
                    "end_date": None,
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["name"] == "Paracetamol"
    assert body["expired"] is False
    assert len(body["schedules"]) == 1

    listed = client.get("/medicines", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == body["id"]

    fetched = client.get(f"/medicines/{body['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["barcode"] == "8901234567890"


def test_update_and_delete_medicine(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    created = client.post("/medicines", headers=headers, json={"name": "Vitamin D3", "strength": "1000 IU"})
    medicine_id = created.json()["id"]

    updated = client.put(f"/medicines/{medicine_id}", headers=headers, json={"strength": "2000 IU"})
    assert updated.status_code == 200
    assert updated.json()["strength"] == "2000 IU"

    deleted = client.delete(f"/medicines/{medicine_id}", headers=headers)
    assert deleted.status_code == 200
    missing = client.get(f"/medicines/{medicine_id}", headers=headers)
    assert missing.status_code == 404
