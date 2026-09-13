from datetime import date, datetime, time

from app.services.analytics import adherence_percentage
from app.services.schedules import occurs_on
from app.models.entities import Schedule
from tests.conftest import auth_header, register


def test_adherence_percentage():
    assert adherence_percentage(8, 2) == 80.0
    assert adherence_percentage(0, 0) == 0.0
    assert adherence_percentage(3, 1) == 75.0


def test_weekly_schedule_occurrence():
    start = date(2026, 8, 31)
    schedule = Schedule(
        medicine_id=1,
        time=time(9, 0),
        frequency="weekly",
        start_date=start,
        end_date=None,
    )
    assert occurs_on(schedule, start) is True
    assert occurs_on(schedule, date(2026, 9, 7)) is True
    assert occurs_on(schedule, date(2026, 9, 1)) is False


def test_analytics_endpoint(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    today = date.today().isoformat()
    created = client.post(
        "/medicines",
        headers=headers,
        json={
            "name": "Paracetamol",
            "strength": "500 mg",
            "expiry_date": today,
            "schedules": [
                {
                    "time": "08:00:00",
                    "frequency": "daily",
                    "start_date": today,
                    "end_date": None,
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    analytics = client.get("/analytics", headers=headers)
    assert analytics.status_code == 200, analytics.text
    body = analytics.json()
    assert "adherence_percentage" in body
    assert "today_medicines" in body
    assert isinstance(body["today_medicines"], list)
    client.post(
        "/dose-history",
        headers=headers,
        json={
            "medicine_id": created.json()["id"],
            "scheduled_time": datetime.combine(date.today(), time(8, 0)).isoformat(),
            "status": "taken",
            "verification_result": "match",
        },
    )
    after = client.get("/analytics", headers=headers).json()
    assert after["taken_count"] >= 1
