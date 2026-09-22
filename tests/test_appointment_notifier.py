from types import SimpleNamespace

from healthtext.appointment_notifier import notify_appointment
from healthtext.models import AppointmentReminder


class DeliveryDouble:
    def __init__(self) -> None:
        self.sent_payload: dict[str, object] | None = None
        self.metric_payload: dict[str, object] | None = None
        self.infrai = SimpleNamespace(
            sms=SimpleNamespace(
                batch=SimpleNamespace(send=self.send),
                events=self.events,
            ),
            metrics=SimpleNamespace(report=self.report),
        )

    def send(self, payload: dict[str, object]) -> dict[str, object]:
        self.sent_payload = payload
        return {"message_id": "msg-42"}

    def events(self, message_id: str) -> dict[str, object]:
        assert message_id == "msg-42"
        return {"events": [{"status": "delivered"}]}

    def report(self, payload: dict[str, object]) -> dict[str, object]:
        self.metric_payload = payload
        return {"accepted": True}


def test_delivered_reminder_reports_one_metric_and_omits_clinical_detail() -> None:
    client = DeliveryDouble()
    reminder = AppointmentReminder("appt-7", "+15551234567", "Harbor Care", "Friday 09:00")

    result = notify_appointment(client, reminder)

    assert result.status == "delivered"
    assert client.sent_payload is not None
    assert client.sent_payload["idempotency_key"] == "appt-7"
    assert "diagnosis" not in str(client.sent_payload["messages"])
    assert client.metric_payload == {
        "name": "appointments.sms_requested",
        "value": 1,
        "type": "counter",
        "tags": {"clinic": "Harbor Care"},
        "idempotency_key": "appt-7",
    }
