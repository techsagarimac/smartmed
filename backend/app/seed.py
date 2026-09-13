"""Development seed data. Passwords come from environment variables."""

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Caregiver, DoseHistory, Medicine, Schedule, User
from app.services.auth import hash_password


def seed_if_empty(db: Session) -> None:
    settings = get_settings()
    if not settings.seed_demo:
        return
    if db.query(User).first():
        return

    user = User(
        name="Priya Sharma",
        email=settings.demo_email.lower(),
        password_hash=hash_password(settings.demo_password),
    )
    db.add(user)
    db.flush()

    today = date.today()
    now = datetime.now().replace(second=0, microsecond=0)

    paracetamol = Medicine(
        user_id=user.id,
        name="Paracetamol",
        strength="500 mg",
        instructions="Take with water after food. Saved from the user's prescription record.",
        expiry_date=today + timedelta(days=180),
        barcode=None,
    )
    metformin = Medicine(
        user_id=user.id,
        name="Metformin",
        strength="500 mg",
        instructions="Take with meals as already prescribed.",
        expiry_date=today + timedelta(days=90),
        barcode="8901234567890",
    )
    atorvastatin = Medicine(
        user_id=user.id,
        name="Atorvastatin",
        strength="10 mg",
        instructions="Evening dose as already prescribed.",
        expiry_date=today + timedelta(days=8),
        barcode=None,
    )
    vitamin_d = Medicine(
        user_id=user.id,
        name="Vitamin D3",
        strength="60000 IU",
        instructions="Weekly capsule as already prescribed.",
        expiry_date=today + timedelta(days=365),
        barcode=None,
    )
    cetirizine = Medicine(
        user_id=user.id,
        name="Cetirizine",
        strength="10 mg",
        instructions="Use only as already directed on the saved record.",
        expiry_date=today - timedelta(days=12),
        barcode="8909876543210",
    )
    db.add_all([paracetamol, metformin, atorvastatin, vitamin_d, cetirizine])
    db.flush()

    start = today - timedelta(days=14)
    db.add_all(
        [
            Schedule(medicine_id=paracetamol.id, time=time(8, 0), frequency="daily", start_date=start, end_date=None),
            Schedule(medicine_id=paracetamol.id, time=time(20, 0), frequency="daily", start_date=start, end_date=None),
            Schedule(medicine_id=metformin.id, time=time(8, 0), frequency="daily", start_date=start, end_date=None),
            Schedule(medicine_id=metformin.id, time=time(14, 0), frequency="daily", start_date=start, end_date=None),
            Schedule(medicine_id=atorvastatin.id, time=time(21, 0), frequency="daily", start_date=start, end_date=None),
            Schedule(
                medicine_id=vitamin_d.id,
                time=time(9, 0),
                frequency="weekly",
                start_date=today - timedelta(days=(today.weekday())),
                end_date=None,
            ),
        ]
    )

    history_rows = []
    for offset in range(1, 8):
        day = today - timedelta(days=offset)
        taken_kwargs = dict(status="taken", verification_result="match")
        history_rows.extend(
            [
                DoseHistory(
                    medicine_id=paracetamol.id,
                    scheduled_time=datetime.combine(day, time(8, 0)),
                    actual_time=datetime.combine(day, time(8, 6)),
                    **taken_kwargs,
                ),
                DoseHistory(
                    medicine_id=paracetamol.id,
                    scheduled_time=datetime.combine(day, time(20, 0)),
                    actual_time=datetime.combine(day, time(20, 11)),
                    **taken_kwargs,
                ),
                DoseHistory(
                    medicine_id=metformin.id,
                    scheduled_time=datetime.combine(day, time(8, 0)),
                    actual_time=datetime.combine(day, time(8, 9)),
                    **taken_kwargs,
                ),
                DoseHistory(
                    medicine_id=atorvastatin.id,
                    scheduled_time=datetime.combine(day, time(21, 0)),
                    actual_time=datetime.combine(day, time(21, 5)),
                    status="taken",
                    verification_result="skipped_verification",
                ),
            ]
        )
        metformin_afternoon = datetime.combine(day, time(14, 0))
        if offset == 1:
            history_rows.append(
                DoseHistory(
                    medicine_id=metformin.id,
                    scheduled_time=metformin_afternoon,
                    actual_time=None,
                    status="missed",
                    verification_result="not_scanned",
                )
            )
        else:
            history_rows.append(
                DoseHistory(
                    medicine_id=metformin.id,
                    scheduled_time=metformin_afternoon,
                    actual_time=metformin_afternoon + timedelta(minutes=8),
                    **taken_kwargs,
                )
            )
    weekly_day = today - timedelta(days=today.weekday())
    if weekly_day < today:
        history_rows.append(
            DoseHistory(
                medicine_id=vitamin_d.id,
                scheduled_time=datetime.combine(weekly_day, time(9, 0)),
                actual_time=datetime.combine(weekly_day, time(9, 10)),
                status="taken",
                verification_result="match",
            )
        )
    db.add_all(history_rows)

    morning = datetime.combine(today, time(8, 0))
    if morning < now:
        db.add(
            DoseHistory(
                medicine_id=paracetamol.id,
                scheduled_time=morning,
                actual_time=morning + timedelta(minutes=6),
                status="taken",
                verification_result="match",
            )
        )

    db.add(
        Caregiver(
            user_id=user.id,
            caregiver_name="Rahul Sharma",
            caregiver_contact="rahul.caregiver@example.com",
            notifications_enabled=True,
        )
    )
    db.commit()
