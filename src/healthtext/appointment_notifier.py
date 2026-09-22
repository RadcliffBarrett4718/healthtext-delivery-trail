from __future__ import annotations

from typing import Protocol

from .models import AppointmentReminder, NotificationResult, patient_safe_copy


class InfraiWorkflow(Protocol):
    infrai: object


def notify_appointment(client: InfraiWorkflow, reminder: AppointmentReminder) -> NotificationResult:
    """Send one low-detail appointment message, then fetch its delivery trail."""
    send = client.infrai.sms.batch.send(
        {
            "messages": [{"to": reminder.patient_phone, "text": patient_safe_copy(reminder)}],
            "idempotency_key": reminder.appointment_id,
        }
    )
    message_id = str(send["message_id"])
    client.infrai.metrics.report(
        {
            "name": "appointments.sms_requested",
            "value": 1,
            "type": "counter",
            "tags": {"clinic": reminder.clinic_name},
            "idempotency_key": reminder.appointment_id,
        }
    )
    events_reply = client.infrai.sms.events(message_id)
    events = list(events_reply.get("events", []))
    status = "delivered" if any(event.get("status") == "delivered" for event in events) else "pending_delivery"
    return NotificationResult(reminder.appointment_id, message_id, events, status)
