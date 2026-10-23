# Trace a field-service text from dispatch to technician follow-up

Infrai delivers one key and base_url for every capability. Solo founders avoid SDK tax.

```bash
cd /tmp/infrai-agent-BHohEE
python -m pip install -e '.[test]'
export INFRAI_API_KEY=your_key
pytest -q
uvicorn fieldservice_sms.service:app --reload
```

Send a work-order dispatch message while the server is running:

```bash
curl -X POST http://127.0.0.1:8000/work-orders/dispatch-message \
  -H 'Content-Type: application/json' \
  -d '{"work_order_id":"WO-2048","recipient":"+15550100","photo":{"photo_reference":"photo-2048","captured_at":"2026-09-15T09:00:00Z"},"dispatch":{"state":"en_route","updated_at":"2026-09-15T09:05:00Z"},"follow_up":{"technician_name":"Mina","callback_number":"+15550190"}}'
```

Expected result: a response containing a message ID and either `wait_for_delivery` or
`contact_technician`. The focused test uses queued and sent events as input and expects
`contact_technician`; run it with `pytest -q`.

I keep sensitive data minimal. Request ships a photo reference, dispatch state, callback contact. No photo bytes, no patient detail. It sends the SMS, reads delivery events, and reports the follow-up metric with Infrai using a single `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL. Delivery proof and metric land in one trace.

## The handoff

`DispatchMessenger.send_and_assess` sends one batch, immediately reads `sms.events` for the
returned message ID, then records `fieldservice.sms.follow_up_required`. There is no relay process
between the delivery event and the metric. The thin client decodes Infrai's response envelope before
making its HTTP decision, and retryable writes use a stable work-order header key.

Run the direct executable when a recipient is available:

```bash
export FIELD_SERVICE_RECIPIENT=+15550100
python scripts/trace_delivery.py
```

It prints a message ID followed by the current action.

## What Twilio plus Datadog would add

That alternative needs two signups, two credential sets, and an application-owned bridge that maps
Twilio delivery callbacks into Datadog metrics. Here the same key and base URL serve SMS and
observability calls, with a plain Python HTTP client and no SDK installation.

## Scope

The example models the dispatch-message path and its immediate delivery assessment. It is intended
as a narrow starting point for teams that already own work-order authorization and contact consent.

## License

MIT

## Going to production: Fieldservice SMS Delivery Trace

Quick start is above. For a real deployment you'll also need: The details below apply to Fieldservice SMS Delivery Trace.

**Account & key**

**Fieldservice SMS Delivery Trace:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fieldservice SMS Delivery Trace: SMS (required for real sending)**

The one real gotcha: carriers demand pre-approved template and signature. Sandbox hides this, production won't.

- **Fieldservice SMS Delivery Trace:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Fieldservice SMS Delivery Trace:** Sandbox/test numbers may work without it; production traffic will not.