"""Optional caregiver alerts for missed recorded doses.

If SMTP is not configured, the alert is recorded in the API response only.
The message never tells a caregiver that a medicine is safe or unsafe.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Caregiver, User
from app.schemas import CaregiverAlert

logger = logging.getLogger("smartmed.notifications")


def notify_caregivers(db: Session, user: User, message: str) -> list[CaregiverAlert]:
    caregivers = (
        db.query(Caregiver)
        .filter(Caregiver.user_id == user.id, Caregiver.notifications_enabled.is_(True))
        .all()
    )
    alerts: list[CaregiverAlert] = []
    for caregiver in caregivers:
        status, detail = _deliver(caregiver, message)
        alerts.append(
            CaregiverAlert(
                caregiver_name=caregiver.caregiver_name,
                caregiver_contact=caregiver.caregiver_contact,
                status=status,
                detail=detail,
            )
        )
    return alerts


def _deliver(caregiver: Caregiver, message: str) -> tuple[str, str]:
    settings = get_settings()
    contact = caregiver.caregiver_contact.strip()
    looks_like_email = "@" in contact and "." in contact.split("@")[-1]
    if not looks_like_email:
        logger.info("Caregiver alert logged for %s (%s): %s", caregiver.caregiver_name, contact, message)
        return "logged", "Contact is not an email address, so the alert was logged only."
    if not settings.smtp_configured:
        logger.info("Caregiver email skipped (SMTP not configured) for %s: %s", contact, message)
        return "logged", "SMTP is not configured. The alert was logged and not emailed."
    try:
        email = EmailMessage()
        email["Subject"] = "SmartMed schedule alert"
        email["From"] = settings.smtp_from or settings.smtp_user
        email["To"] = contact
        email.set_content(message)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(email)
        return "sent", "Email sent."
    except Exception as exc:
        logger.exception("Caregiver email failed for %s", contact)
        return "failed", f"Email could not be sent: {exc}"
