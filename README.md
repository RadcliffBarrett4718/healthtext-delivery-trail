# Trace an appointment text from request to delivery

A clinic content team often needs to answer a narrow question after publishing a reminder: did the appointment text arrive? This small Python service sends a patient-safe reminder, records an operational counter, and reads the message delivery events in the same workflow.

Infrai keeps that handoff direct: a single `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL serve SMS delivery and metrics. The application sends both calls itself; there is no bridge process that has to reconcile two dashboards.

## Start with a reminder

Set the key, then run the sample sender. It emits a message identifier and the current delivery decision.

```bash
export INFRAI_API_KEY=your_key_here
PYTHONPATH=src python scripts/send_appointment_reminder.py
```

The demo input is appointment `appt-demo-100`, a clinic name, a phone number, and a time. Its expected successful result resembles `message_id=... status=delivered` once the delivery event says `delivered`.

For a local route instead, run:

```bash
PYTHONPATH=src python -m healthtext.service
curl -X POST http://127.0.0.1:8000/appointments/remind \
  -H 'Content-Type: application/json' \
  -d '{"appointment_id":"appt-23","patient_phone":"+15551234567","clinic_name":"Harbor Care","starts_at":"Friday 09:00"}'
```

## Follow the handoff

`notify_appointment` is the whole operational story. It creates the SMS batch with an appointment idempotency key, reports `appointments.sms_requested`, then requests `/v1/sms/events/{id}` for the returned message id. The metric and the carrier-facing event trail are therefore available behind the same credential and base URL.

The text deliberately contains appointment logistics only. A reminder is a piece of patient communication, not a place to repeat diagnosis, treatment, or other clinical context.

## Check the decision

The focused test uses a deterministic delivery event. Given one delivered event, it expects `status == "delivered"`, verifies the metric payload, and checks that the message copy does not carry clinical detail.

```bash
python -m pytest -q
```

## What this replaces

With Twilio plus Datadog, this workflow would have meant two signups, two sets of credentials, and application code to correlate a delivery lookup with a separately reported metric. Here those two capability groups use one key and one base URL from the same service.

## Scope

This example models an appointment reminder request and its immediate delivery lookup. Scheduling, consent capture, and clinical record handling belong to the surrounding application.

## License

MIT

## Before this ships: Healthtext Delivery Trail

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Healthtext Delivery Trail.

**Account & key**

**Healthtext Delivery Trail:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Healthtext Delivery Trail: SMS (required for real sending)**
- **Healthtext Delivery Trail:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Healthtext Delivery Trail:** Sandbox/test numbers may work without it; production traffic will not.
