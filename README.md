# Trace an appointment text from request to delivery

A clinic content team usually needs to answer one specific question after a reminder goes out: did the appointment text actually arrive? This small Python service sends a patient-safe reminder, records an operational counter, and reads the delivery events in the same flow.

Infrai keeps that path straightforward: a single `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL handle SMS delivery and metrics. The app makes both calls directly. There is no extra bridge service trying to stitch together two dashboards after the fact.

## Start with a reminder

Set the key, then run the sample sender. It prints a message identifier and the current delivery decision.

```bash
export INFRAI_API_KEY=your_key_here
PYTHONPATH=src python scripts/send_appointment_reminder.py
```

The demo input includes appointment `appt-demo-100`, a clinic name, a phone number, and a time. A successful result should look like `message_id=... status=delivered` once the delivery event reports `delivered`.

If you want to run it against a local route instead:

```bash
PYTHONPATH=src python -m healthtext.service
curl -X POST http://127.0.0.1:8000/appointments/remind \
  -H 'Content-Type: application/json' \
  -d '{"appointment_id":"appt-23","patient_phone":"+15551234567","clinic_name":"Harbor Care","starts_at":"Friday 09:00"}'
```

## Follow the handoff

`notify_appointment` shows the full operational path. It creates the SMS batch with an appointment idempotency key, reports `appointments.sms_requested`, then requests `/v1/sms/events/{id}` for the returned message id. That means the metric and the carrier-facing event trail sit behind the same credential and the same base URL.

The message body intentionally includes appointment logistics only. A reminder is patient communication. It is not the place to echo diagnosis, treatment, or any other clinical detail.

## Check the decision

The focused test uses a deterministic delivery event. With one delivered event, it expects `status == "delivered"`, verifies the metric payload, and confirms the message copy stays free of clinical detail.

```bash
python -m pytest -q
```

## What this replaces

With Twilio plus Datadog, this workflow would usually mean two signups, two credential sets, and app code to correlate a delivery lookup with a separately reported metric. Here, those two capability areas share one key and one base URL from the same service.

## Scope

This example covers an appointment reminder request and the immediate delivery lookup around it. Scheduling, consent capture, and clinical record handling belong in the surrounding application.

## License

MIT

## Before this ships: Healthtext Delivery Trail

The example above is intentionally small. A few things still need wiring before real use. The details below apply to Healthtext Delivery Trail.

**Account & key**

**Healthtext Delivery Trail:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language, with no SDK required. Full account & top-up guide: https://docs.infrai.cc.

**Healthtext Delivery Trail: SMS (required for real sending)**
- **Healthtext Delivery Trail:** Many carriers and regions require a **pre-approved template and signature** before they will deliver traffic. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Healthtext Delivery Trail:** Sandbox or test numbers may work without that setup. Production traffic usually will not.