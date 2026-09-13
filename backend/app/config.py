"""Application settings. Secrets come from environment variables, not source code."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
        case_sensitive=False,
    )

    app_name: str = "SmartMed"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", alias="SMARTMED_ENV")

    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    database_url: str = "sqlite:///./data/smartmed.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    tesseract_cmd: str = Field(default="", alias="TESSERACT_CMD")
    max_image_mb: int = 8
    ocr_min_confidence: float = 40.0
    match_name_threshold: float = 0.72
    match_name_with_strength_threshold: float = 0.55
    reminder_grace_minutes: int = 45
    missed_lookback_days: int = 2
    expiry_warning_days: int = 14

    seed_demo: bool = Field(default=True, alias="SMARTMED_SEED")
    demo_email: str = Field(default="demo@smartmed.local", alias="DEMO_EMAIL")
    demo_password: str = Field(default="DemoPass123", alias="DEMO_PASSWORD")

    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="", alias="SMTP_FROM")
    smtp_starttls: bool = Field(default=True, alias="SMTP_STARTTLS")

    @field_validator("jwt_secret")
    @classmethod
    def secret_must_be_set(cls, value: str) -> str:
        if not value or value.strip() == "":
            raise ValueError(
                "JWT_SECRET is missing. Copy backend/.env.example to backend/.env "
                "and set JWT_SECRET to a long random string."
            )
        if value.strip() in {"change-me", "secret", "password"}:
            raise ValueError("JWT_SECRET is too weak. Generate a random value.")
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def data_dir(self) -> Path:
        return BACKEND_DIR / "data"

    @property
    def upload_dir(self) -> Path:
        return BACKEND_DIR / "uploads"

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and (self.smtp_from or self.smtp_user))


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
