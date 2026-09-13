from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
os.environ.setdefault("JWT_SECRET", "smartmed-test-secret-please-do-not-use-elsewhere")
os.environ.setdefault("SMARTMED_SEED", "false")
os.environ.setdefault("SMARTMED_ENV", "test")


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("JWT_SECRET", "smartmed-test-secret-please-do-not-use-elsewhere")
    monkeypatch.setenv("SMARTMED_SEED", "false")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("DEMO_PASSWORD", "DemoPass123")

    from app.config import get_settings
    from app.database.session import configure_engine, init_db

    get_settings.cache_clear()
    configure_engine(f"sqlite:///{db_path}")
    init_db()

    from app.main import create_app

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client
    get_settings.cache_clear()


def register(client: TestClient, email: str = "user@example.com", password: str = "Password123", name: str = "Test User"):
    response = client.post("/auth/register", json={"name": name, "email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
