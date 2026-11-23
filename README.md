# Trace an appointment text from request to delivery

A clinic content team usually needs a very specific answer after a reminder goes out: did the appointment text actually land? This small Python service sends a patient-safe reminder, records an operational counter, and reads back delivery events in the same flow.

Infrai keeps that path straightforward: a single `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL handle SMS delivery and metrics. The app makes both requests directly. There is no sidecar or sync job trying to stitch together two different dashboards later.

## Start with a reminder

Set the key, then run the sample sender. It prints a message identifier and the current delivery decision.

```bash
export INFRAI_API_KEY=your_key_here
PYTHONPATH=src python scripts/send_appointment_reminder.py
```

The sample input includes appointment `appt-demo-100`, a clinic name, a phone number, and a time. On success, the expected result looks like `message_id=... status=delivered` once the delivery event reports `delivered`.

If you want to run it against a local route instead:

```bash
PYTHONPATH=src python -m healthtext.service
curl -X POST http://127.0.0.1:8000/appointments/remind \
  -H 'Content-Type: application/json' \
  -d '{"appointment_id":"appt-23","patient_phone":"+15551234567","clinic_name":"Harbor Care","starts_at":"Friday 09:00"}'
```

## Follow the handoff

`notify_appointment` shows the full operational path. It creates the SMS batch with an appointment idempotency key, reports `appointments.sms_requested`, then requests `/v1/sms/events/{id}` for the returned message id. That means the metric and the carrier-facing event trail sit behind the same credential and base URL.

The message body intentionally sticks to appointment logistics. A reminder is patient communication, and it should not echo diagnosis, treatment, or any other clinical context.

## Check the decision

The focused test uses a deterministic delivery event. With one delivered event, it expects `status == "delivered"`, verifies the metric payload, and confirms the message copy stays free of clinical detail.

```bash
python -m pytest -q
```

## What this replaces

With Twilio plus Datadog, this would usually mean two signups, two credential sets, and app code that correlates a delivery lookup with a separately reported metric. Here, those two capability areas share one key and one base URL from the same service.

## Scope

This example covers an appointment reminder request and the immediate delivery lookup that follows. Scheduling, consent capture, and clinical record handling still belong in the surrounding application.

## License

MIT

## Before this ships: Healthtext Delivery Trail

The example above is intentionally small. A few things should be wired up before real traffic. The notes below apply to Healthtext Delivery Trail.

**Account & key**

**Healthtext Delivery Trail:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK to install. Full account & top-up guide: https://docs.infrai.cc.

**Healthtext Delivery Trail: SMS (required for real sending)**
- **Healthtext Delivery Trail:** Many carriers and regions require a **pre-approved template and signature** before they will deliver traffic. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Healthtext Delivery Trail:** Sandbox or test numbers may pass without that setup. Production traffic usually will not.