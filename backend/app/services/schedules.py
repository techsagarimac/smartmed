"""Turn saved schedules into concrete reminder slots for a calendar window."""

from __future__ import annotations

from datetime import date, datetime, timedelta, time

from app.models import DoseHistory, Medicine, Schedule

VALID_FREQUENCIES = {"daily", "weekly", "every_other_day"}


def combine_local(day: date, at: time) -> datetime:
    return datetime(day.year, day.month, day.day, at.hour, at.minute, at.second)


def schedule_is_active(schedule: Schedule, day: date) -> bool:
    if day < schedule.start_date:
        return False
    if schedule.end_date and day > schedule.end_date:
        return False
    return True


def occurs_on(schedule: Schedule, day: date) -> bool:
    if not schedule_is_active(schedule, day):
        return False
    frequency = (schedule.frequency or "daily").lower()
    delta = (day - schedule.start_date).days
    if frequency == "daily":
        return True
    if frequency == "weekly":
        return delta % 7 == 0
    if frequency == "every_other_day":
        return delta % 2 == 0
    return False


def iter_slots(schedule: Schedule, start: date, end: date) -> list[datetime]:
    if end < start:
        return []
    slots: list[datetime] = []
    day = start
    while day <= end:
        if occurs_on(schedule, day):
            slots.append(combine_local(day, schedule.time))
        day += timedelta(days=1)
    return slots


def slot_key(medicine_id: int, scheduled_time: datetime) -> tuple[int, datetime]:
    return medicine_id, scheduled_time


def history_map(records: list[DoseHistory]) -> dict[tuple[int, datetime], DoseHistory]:
    mapping: dict[tuple[int, datetime], DoseHistory] = {}
    for record in records:
        mapping[slot_key(record.medicine_id, record.scheduled_time)] = record
    return mapping


def medicines_for_user(medicines: list[Medicine]) -> list[Medicine]:
    return medicines


def validate_frequency(frequency: str) -> str:
    cleaned = frequency.strip().lower().replace("-", "_").replace(" ", "_")
    if cleaned not in VALID_FREQUENCIES:
        raise ValueError("Frequency must be daily, weekly, or every_other_day.")
    return cleaned
