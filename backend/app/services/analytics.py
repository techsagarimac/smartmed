"""Dashboard analytics and missed-dose reconciliation."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.models import DoseHistory, Medicine, User
from app.schemas import (
    AnalyticsResponse,
    DoseHistoryOut,
    MedicineOut,
    ReminderItem,
)
from app.services.notifications import notify_caregivers
from app.services.schedules import history_map, iter_slots, slot_key
from app.ocr.pipeline import tesseract_available


def now_local() -> datetime:
    return datetime.now().replace(microsecond=0)


def today_local() -> date:
    return now_local().date()


def is_expired(medicine: Medicine, on: date | None = None) -> bool:
    if medicine.expiry_date is None:
        return False
    return medicine.expiry_date < (on or today_local())


def is_expiring_soon(medicine: Medicine, on: date | None = None) -> bool:
    if medicine.expiry_date is None or is_expired(medicine, on):
        return False
    horizon = (on or today_local()) + timedelta(days=get_settings().expiry_warning_days)
    return medicine.expiry_date <= horizon


def serialize_medicine(medicine: Medicine) -> MedicineOut:
    payload = MedicineOut.model_validate(medicine)
    payload.expired = is_expired(medicine)
    payload.expiring_soon = is_expiring_soon(medicine)
    return payload


def serialize_history(record: DoseHistory) -> DoseHistoryOut:
    return DoseHistoryOut(
        id=record.id,
        medicine_id=record.medicine_id,
        medicine_name=record.medicine.name if record.medicine else "",
        medicine_strength=record.medicine.strength if record.medicine else "",
        scheduled_time=record.scheduled_time,
        actual_time=record.actual_time,
        status=record.status,
        verification_result=record.verification_result,
    )


def load_user_medicines(db: Session, user: User) -> list[Medicine]:
    return (
        db.query(Medicine)
        .options(selectinload(Medicine.schedules), selectinload(Medicine.dose_history))
        .filter(Medicine.user_id == user.id)
        .order_by(Medicine.name.asc())
        .all()
    )


def expected_slots(medicines: list[Medicine], start: date, end: date) -> list[tuple[Medicine, datetime, int]]:
    items: list[tuple[Medicine, datetime, int]] = []
    for medicine in medicines:
        for schedule in medicine.schedules:
            for slot in iter_slots(schedule, start, end):
                items.append((medicine, slot, schedule.id))
    items.sort(key=lambda item: item[1])
    return items


def reminder_from(medicine: Medicine, slot: datetime, schedule_id: int, record: DoseHistory | None, current: datetime) -> ReminderItem:
    if record:
        status = record.status
        verification = record.verification_result
        history_id = record.id
    elif slot <= current:
        status = "due" if slot + timedelta(minutes=get_settings().reminder_grace_minutes) >= current else "overdue"
        verification = None
        history_id = None
    else:
        status = "upcoming"
        verification = None
        history_id = None
    return ReminderItem(
        medicine_id=medicine.id,
        medicine_name=medicine.name,
        strength=medicine.strength,
        instructions=medicine.instructions,
        schedule_id=schedule_id,
        scheduled_time=slot,
        status=status,
        expired=is_expired(medicine),
        verification_result=verification,
        dose_history_id=history_id,
    )


def reconcile_missed_doses(db: Session, user: User) -> list[DoseHistory]:
    settings = get_settings()
    current = now_local()
    start = current.date() - timedelta(days=settings.missed_lookback_days)
    medicines = load_user_medicines(db, user)
    records = [item for medicine in medicines for item in medicine.dose_history]
    existing = history_map(records)
    created: list[DoseHistory] = []
    grace = timedelta(minutes=settings.reminder_grace_minutes)

    for medicine, slot, _schedule_id in expected_slots(medicines, start, current.date()):
        if slot + grace >= current:
            continue
        key = slot_key(medicine.id, slot)
        if key in existing:
            continue
        row = DoseHistory(
            medicine_id=medicine.id,
            scheduled_time=slot,
            actual_time=None,
            status="missed",
            verification_result="not_scanned",
        )
        db.add(row)
        db.flush()
        existing[key] = row
        created.append(row)
        notify_caregivers(
            db,
            user,
            (
                f"SmartMed reminder: {user.name}'s saved medicine '{medicine.name}' "
                f"was not recorded as taken at {slot.strftime('%Y-%m-%d %H:%M')}. "
                "This is a schedule notification only, not medical advice."
            ),
        )
    if created:
        db.commit()
        for row in created:
            db.refresh(row)
    return created


def build_analytics(db: Session, user: User) -> AnalyticsResponse:
    reconcile_missed_doses(db, user)
    current = now_local()
    today = current.date()
    medicines = load_user_medicines(db, user)
    records = [item for medicine in medicines for item in medicine.dose_history]
    existing = history_map(records)

    today_items = [
        reminder_from(medicine, slot, schedule_id, existing.get(slot_key(medicine.id, slot)), current)
        for medicine, slot, schedule_id in expected_slots(medicines, today, today)
    ]

    upcoming = next((item for item in today_items if item.status in {"upcoming", "due"}), None)
    if upcoming is None:
        tomorrow = today + timedelta(days=1)
        later = expected_slots(medicines, tomorrow, tomorrow + timedelta(days=6))
        if later:
            medicine, slot, schedule_id = later[0]
            upcoming = reminder_from(medicine, slot, schedule_id, None, current)

    week_start = today - timedelta(days=6)
    week_slots = expected_slots(medicines, week_start, today)
    taken = missed = skipped = pending = 0
    for medicine, slot, _schedule_id in week_slots:
        record = existing.get(slot_key(medicine.id, slot))
        if record:
            if record.status == "taken":
                taken += 1
            elif record.status == "missed":
                missed += 1
            elif record.status == "skipped":
                skipped += 1
        elif slot < current:
            missed += 1
        else:
            pending += 1

    denominator = taken + missed
    adherence = round((taken / denominator) * 100, 1) if denominator else 0.0

    recent = sorted(records, key=lambda row: row.scheduled_time, reverse=True)[:12]
    expiring = [
        serialize_medicine(medicine)
        for medicine in medicines
        if is_expired(medicine) or is_expiring_soon(medicine)
    ]
    expiring.sort(key=lambda item: item.expiry_date or date.max)

    return AnalyticsResponse(
        today_medicines=today_items,
        upcoming=upcoming,
        taken_count=sum(1 for item in today_items if item.status == "taken"),
        missed_count=sum(1 for item in today_items if item.status == "missed"),
        skipped_count=sum(1 for item in today_items if item.status == "skipped"),
        pending_count=sum(1 for item in today_items if item.status in {"due", "overdue", "upcoming"}),
        adherence_percentage=adherence,
        adherence_window_days=7,
        expiring_medicines=expiring,
        recent_history=[serialize_history(row) for row in recent],
        weekly_counts={"taken": taken, "missed": missed, "skipped": skipped, "pending": pending},
        smtp_configured=get_settings().smtp_configured,
        ocr_available=tesseract_available(),
    )


def list_reminders(db: Session, user: User) -> list[ReminderItem]:
    analytics = build_analytics(db, user)
    return analytics.today_medicines


def adherence_percentage(taken: int, missed: int) -> float:
    denominator = taken + missed
    if denominator <= 0:
        return 0.0
    return round((taken / denominator) * 100, 1)
