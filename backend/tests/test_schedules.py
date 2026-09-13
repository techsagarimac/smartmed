from datetime import date, timedelta

from tests.conftest import auth_header, register


def _medicine(client, headers):
    response = client.post("/medicines", headers=headers, json={"name": "Metformin", "strength": "500 mg"})
    return response.json()["id"]


def test_create_schedule(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    medicine_id = _medicine(client, headers)
    start = date.today().isoformat()
    created = client.post(
        "/schedules",
        headers=headers,
        json={
            "medicine_id": medicine_id,
            "time": "14:00:00",
            "frequency": "daily",
            "start_date": start,
            "end_date": None,
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["frequency"] == "daily"

    listed = client.get("/schedules", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["medicine_id"] == medicine_id


def test_invalid_schedule_end_date(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    medicine_id = _medicine(client, headers)
    response = client.post(
        "/schedules",
        headers=headers,
        json={
            "medicine_id": medicine_id,
            "time": "08:00:00",
            "frequency": "daily",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 422


def test_reject_unknown_frequency(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    medicine_id = _medicine(client, headers)
    response = client.post(
        "/schedules",
        headers=headers,
        json={
            "medicine_id": medicine_id,
            "time": "08:00:00",
            "frequency": "hourly",
            "start_date": date.today().isoformat(),
        },
    )
    assert response.status_code == 422
