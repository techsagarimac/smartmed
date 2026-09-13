"""SQLite engine and session helpers."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = None
SessionLocal = None


def _sqlite_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def build_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    new_engine = create_engine(url, connect_args=_sqlite_connect_args(url), future=True)

    if url.startswith("sqlite"):

        @event.listens_for(new_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return new_engine


def configure_engine(database_url: str | None = None) -> None:
    global engine, SessionLocal
    engine = build_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _ensure_engine() -> None:
    if engine is None or SessionLocal is None:
        configure_engine()


def get_db() -> Generator[Session, None, None]:
    _ensure_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    _ensure_engine()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    from app.models import entities  # noqa: F401

    _ensure_engine()
    get_settings().data_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
