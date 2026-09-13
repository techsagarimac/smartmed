from tests.conftest import auth_header, register


def test_register_and_login(client):
    created = register(client)
    assert created["token_type"] == "bearer"
    assert created["user"]["email"] == "user@example.com"
    assert "password" not in created["user"]

    login = client.post("/auth/login", json={"email": "user@example.com", "password": "Password123"})
    assert login.status_code == 200
    assert login.json()["user"]["name"] == "Test User"

    me = client.get("/auth/me", headers=auth_header(login.json()["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"


def test_duplicate_register_rejected(client):
    register(client)
    again = client.post(
        "/auth/register",
        json={"name": "Test User", "email": "user@example.com", "password": "Password123"},
    )
    assert again.status_code == 409


def test_login_rejects_wrong_password(client):
    register(client)
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "WrongPass1"})
    assert response.status_code == 401
    assert "Incorrect" in response.json()["detail"]


def test_protected_route_requires_auth(client):
    response = client.get("/medicines")
    assert response.status_code == 401
