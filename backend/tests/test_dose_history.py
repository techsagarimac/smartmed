from datetime import datetime

from tests.conftest import auth_header, register


def test_record_and_list_dose_history(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    medicine = client.post("/medicines", headers=headers, json={"name": "Paracetamol", "strength": "500 mg"}).json()
    scheduled = datetime.now().replace(minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        "/dose-history",
        headers=headers,
        json={
            "medicine_id": medicine["id"],
            "scheduled_time": scheduled,
            "status": "taken",
            "verification_result": "match",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "taken"
    assert created.json()["medicine_name"] == "Paracetamol"

    listed = client.get("/dose-history", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["verification_result"] == "match"


def test_taken_requires_match_or_skip_scan(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    medicine = client.post("/medicines", headers=headers, json={"name": "Paracetamol"}).json()
    response = client.post(
        "/dose-history",
        headers=headers,
        json={
            "medicine_id": medicine["id"],
            "scheduled_time": datetime.now().isoformat(),
            "status": "taken",
            "verification_result": "mismatch",
        },
    )
    assert response.status_code == 422
