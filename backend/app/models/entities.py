"""SQLAlchemy tables for SmartMed.

users, medicines, schedules, dose_history, and caregivers match the project
specification. Relationships use ON DELETE cascade so removing a medicine
also removes its schedules and dose records.
"""

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    medicines: Mapped[list["Medicine"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    caregivers: Mapped[list["Caregiver"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    strength: Mapped[str] = mapped_column(String(80), default="")
    instructions: Mapped[str] = mapped_column(Text, default="")
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="medicines")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="medicine", cascade="all, delete-orphan")
    dose_history: Mapped[list["DoseHistory"]] = relationship(back_populates="medicine", cascade="all, delete-orphan")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id", ondelete="CASCADE"), index=True)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    frequency: Mapped[str] = mapped_column(String(32), default="daily")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    medicine: Mapped["Medicine"] = relationship(back_populates="schedules")


class DoseHistory(Base):
    __tablename__ = "dose_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id", ondelete="CASCADE"), index=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    actual_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    verification_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    medicine: Mapped["Medicine"] = relationship(back_populates="dose_history")

    __table_args__ = (
        UniqueConstraint("medicine_id", "scheduled_time", name="uq_dose_slot"),
    )


class Caregiver(Base):
    __tablename__ = "caregivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    caregiver_name: Mapped[str] = mapped_column(String(120))
    caregiver_contact: Mapped[str] = mapped_column(String(255))
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="caregivers")
