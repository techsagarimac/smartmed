from tests.conftest import register


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unauthenticated_analytics(client):
    register(client)
    response = client.get("/analytics")
    assert response.status_code == 401
