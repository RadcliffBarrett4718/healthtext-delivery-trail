from healthtext.appointment_notifier import notify_appointment
from healthtext.infrai_client import InfraiClient
from healthtext.models import AppointmentReminder


def main() -> None:
    reminder = AppointmentReminder(
        appointment_id="appt-demo-100",
        patient_phone="+15551234567",
        clinic_name="Northside Clinic",
        starts_at="Tuesday 10:30",
    )
    result = notify_appointment(InfraiClient(), reminder)
    print(f"message_id={result.message_id} status={result.status}")


if __name__ == "__main__":
    main()
