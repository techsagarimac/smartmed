"""Pydantic request and response schemas."""

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_FREQUENCIES = {"daily", "weekly", "every_other_day"}
ALLOWED_DOSE_STATUS = {"taken", "missed", "skipped"}
ALLOWED_VERIFICATION = {"match", "mismatch", "skipped_verification", "not_scanned", "low_confidence", "no_text"}


def normalize_email(value: str) -> str:
    cleaned = (value or "").strip().lower()
    if "@" not in cleaned or " " in cleaned or cleaned.startswith("@") or cleaned.endswith("@"):
        raise ValueError("Enter a valid email address.")
    local, _, domain = cleaned.partition("@")
    if not local or "." not in domain:
        raise ValueError("Enter a valid email address.")
    return cleaned


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserPublic(ORMModel):
    id: int
    name: str
    email: str
    created_at: datetime


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str) -> str:
        return normalize_email(value)


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str) -> str:
        return normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class ScheduleBase(BaseModel):
    time: time
    frequency: str = "daily"
    start_date: date
    end_date: Optional[date] = None

    @field_validator("frequency")
    @classmethod
    def frequency_ok(cls, value: str) -> str:
        cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
        if cleaned not in ALLOWED_FREQUENCIES:
            raise ValueError("Frequency must be daily, weekly, or every_other_day.")
        return cleaned

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, value: Optional[date], info):
        start = info.data.get("start_date")
        if value and start and value < start:
            raise ValueError("End date cannot be before the start date.")
        return value


class ScheduleCreate(ScheduleBase):
    medicine_id: int


class ScheduleUpdate(BaseModel):
    time: Optional[time] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("frequency")
    @classmethod
    def frequency_ok(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
        if cleaned not in ALLOWED_FREQUENCIES:
            raise ValueError("Frequency must be daily, weekly, or every_other_day.")
        return cleaned


class ScheduleOut(ORMModel):
    id: int
    medicine_id: int
    time: time
    frequency: str
    start_date: date
    end_date: Optional[date] = None


class MedicineBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    strength: str = Field(default="", max_length=80)
    instructions: str = Field(default="", max_length=2000)
    expiry_date: Optional[date] = None
    barcode: Optional[str] = Field(default=None, max_length=64)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Medicine name is required.")
        return cleaned

    @field_validator("barcode")
    @classmethod
    def barcode_clean(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class MedicineCreate(MedicineBase):
    schedules: list[ScheduleBase] = Field(default_factory=list)


class MedicineUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    strength: Optional[str] = Field(default=None, max_length=80)
    instructions: Optional[str] = Field(default=None, max_length=2000)
    expiry_date: Optional[date] = None
    barcode: Optional[str] = Field(default=None, max_length=64)


class MedicineOut(ORMModel):
    id: int
    user_id: int
    name: str
    strength: str
    instructions: str
    expiry_date: Optional[date] = None
    barcode: Optional[str] = None
    created_at: datetime
    schedules: list[ScheduleOut] = Field(default_factory=list)
    expired: bool = False
    expiring_soon: bool = False


class DoseHistoryCreate(BaseModel):
    medicine_id: int
    scheduled_time: datetime
    status: str
    verification_result: Optional[str] = "not_scanned"

    @field_validator("status")
    @classmethod
    def status_ok(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in ALLOWED_DOSE_STATUS:
            raise ValueError("Status must be taken, missed, or skipped.")
        return cleaned

    @field_validator("verification_result")
    @classmethod
    def verification_ok(cls, value: Optional[str]) -> str:
        cleaned = (value or "not_scanned").strip().lower()
        if cleaned not in ALLOWED_VERIFICATION:
            raise ValueError("Unknown verification result.")
        return cleaned


class DoseHistoryOut(ORMModel):
    id: int
    medicine_id: int
    medicine_name: str
    medicine_strength: str = ""
    scheduled_time: datetime
    actual_time: Optional[datetime] = None
    status: str
    verification_result: Optional[str] = None


class CaregiverCreate(BaseModel):
    caregiver_name: str = Field(min_length=2, max_length=120)
    caregiver_contact: str = Field(min_length=3, max_length=255)
    notifications_enabled: bool = True


class CaregiverUpdate(BaseModel):
    caregiver_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    caregiver_contact: Optional[str] = Field(default=None, min_length=3, max_length=255)
    notifications_enabled: Optional[bool] = None


class CaregiverOut(ORMModel):
    id: int
    user_id: int
    caregiver_name: str
    caregiver_contact: str
    notifications_enabled: bool


class CaregiverAlert(BaseModel):
    caregiver_name: str
    caregiver_contact: str
    status: str
    detail: str


class DetectedMedicine(BaseModel):
    name: Optional[str] = None
    strength: Optional[str] = None
    barcode: Optional[str] = None
    raw_text: str = ""
    ocr_confidence: Optional[float] = None


class ScheduledMedicineInfo(BaseModel):
    id: int
    name: str
    strength: str
    barcode: Optional[str] = None
    expiry_date: Optional[date] = None
    instructions: str = ""


class VerificationResponse(BaseModel):
    result: str
    headline: str
    scheduled_medicine: ScheduledMedicineInfo
    detected: DetectedMedicine
    confidence: Optional[float] = None
    name_similarity: Optional[float] = None
    barcode_matched: Optional[bool] = None
    expired: bool = False
    can_record_dose: bool = False
    disclaimer: str
    guidance: str
    error: Optional[str] = None


class ReminderItem(BaseModel):
    medicine_id: int
    medicine_name: str
    strength: str
    instructions: str
    schedule_id: int
    scheduled_time: datetime
    status: str
    expired: bool = False
    verification_result: Optional[str] = None
    dose_history_id: Optional[int] = None


class AnalyticsResponse(BaseModel):
    today_medicines: list[ReminderItem]
    upcoming: Optional[ReminderItem] = None
    taken_count: int
    missed_count: int
    skipped_count: int
    pending_count: int
    adherence_percentage: float
    adherence_window_days: int = 7
    expiring_medicines: list[MedicineOut]
    recent_history: list[DoseHistoryOut]
    weekly_counts: dict[str, int]
    smtp_configured: bool = False
    ocr_available: bool = True


class MessageResponse(BaseModel):
    detail: str
