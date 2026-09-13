from app.config import get_settings
from app.database.session import configure_engine, init_db
from app.models import User
from app.seed import seed_if_empty


def test_seed_creates_demo_user(tmp_path, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "smartmed-test-secret-please-do-not-use-elsewhere")
    monkeypatch.setenv("SMARTMED_SEED", "true")
    monkeypatch.setenv("DEMO_EMAIL", "demo@smartmed.local")
    monkeypatch.setenv("DEMO_PASSWORD", "DemoPass123")
    get_settings.cache_clear()
    db_path = tmp_path / "seed.db"
    configure_engine(f"sqlite:///{db_path}")
    init_db()
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        seed_if_empty(db)
        user = db.query(User).filter(User.email == "demo@smartmed.local").first()
        assert user is not None
        assert len(user.medicines) >= 4
        assert len(user.caregivers) == 1
        seed_if_empty(db)
        assert db.query(User).count() == 1
    finally:
        db.close()
        get_settings.cache_clear()
