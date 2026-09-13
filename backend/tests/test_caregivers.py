from tests.conftest import auth_header, register


def test_caregiver_crud(client):
    token = register(client)["access_token"]
    headers = auth_header(token)
    created = client.post(
        "/caregivers",
        headers=headers,
        json={
            "caregiver_name": "Rahul Sharma",
            "caregiver_contact": "rahul@example.com",
            "notifications_enabled": True,
        },
    )
    assert created.status_code == 201, created.text
    caregiver_id = created.json()["id"]
    listed = client.get("/caregivers", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["caregiver_name"] == "Rahul Sharma"
    updated = client.put(
        f"/caregivers/{caregiver_id}",
        headers=headers,
        json={"notifications_enabled": False},
    )
    assert updated.json()["notifications_enabled"] is False
    deleted = client.delete(f"/caregivers/{caregiver_id}", headers=headers)
    assert deleted.status_code == 200
