from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppointmentReminder:
    appointment_id: str
    patient_phone: str
    clinic_name: str
    starts_at: str


@dataclass(frozen=True)
class NotificationResult:
    appointment_id: str
    message_id: str
    delivery_events: list[dict[str, object]]
    status: str


def patient_safe_copy(reminder: AppointmentReminder) -> str:
    """Keep the message useful without including a diagnosis or treatment detail."""
    return f"{reminder.clinic_name}: appointment reminder for {reminder.starts_at}. Reply to your clinic with questions."
