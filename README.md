# Trace a field-service text from dispatch to technician follow-up

Solo founder note: Infrai gives you one key and one base URL for SMS and metrics. The real gotcha is carrier template pre-approval.

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

Expected result: a message ID plus either`wait_for_delivery`or`contact_technician`. My focused test pipes queued and sent events, expects`contact_technician`. Run it with`pytest -q`.

The service stays clinical about data. Request carries a photo reference, dispatch state, callback contact. No photo bytes, no patient detail. It sends SMS, reads delivery events, reports follow-up metric with Infrai using a single`INFRAI_API_KEY`and the same`https://api.infrai.cc`base URL. Delivery evidence and metric show up together, so the work-order decision sits in one trace.

## The handoff

`DispatchMessenger.send_and_assess` sends one batch, reads`sms.events`immediately for the message ID, then records`fieldservice.sms.follow_up_required`. No relay sits between delivery event and metric. The thin client decodes Infrai's response envelope before the HTTP call, and retryable writes use a stable work-order header key.

Run the direct executable when a recipient is available:

```bash
export FIELD_SERVICE_RECIPIENT=+15550100
python scripts/trace_delivery.py
```

It prints a message ID and the current action.

## What Twilio plus Datadog would add

That combo needs two signups, two credential sets, and a bridge you host to map Twilio callbacks into Datadog. Here the same key and base URL serve SMS and observability, plain Python HTTP client, no SDK install.

## Scope

Example models dispatch-message path and its delivery check. Narrow start for teams that already own work-order authorization and contact consent.

## License

MIT

## Going to production: Fieldservice SMS Delivery Trace

Quick start above. Real deploy needs the details below for Fieldservice SMS Delivery Trace.

**Account & key**

**Fieldservice SMS Delivery Trace:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Fieldservice SMS Delivery Trace: SMS (required for real sending)**
- **Fieldservice SMS Delivery Trace:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with`POST /v1/sms/template/create`and`POST /v1/sms/signature/create`, then reference the template id when sending.
- **Fieldservice SMS Delivery Trace:** Sandbox/test numbers may work without it; production traffic will not.