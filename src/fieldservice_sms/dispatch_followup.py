from typing import Any

from .infrai import InfraiClient
from .models import DeliveryDecision, WorkOrderMessage


def needs_technician_follow_up(events: list[dict[str, Any]]) -> bool:
    return not any(event.get("status") == "delivered" for event in events)


class DispatchMessenger:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def send_and_assess(self, message: WorkOrderMessage) -> DeliveryDecision:
        infrai = self.client
        sms_payload = {
            "messages": [{
                "to": message.recipient,
                "text": (
                    f"Work order {message.work_order_id}: {message.dispatch.state}. "
                    f"Photo reference: {message.photo.photo_reference}. "
                    f"Technician: {message.follow_up.technician_name}, {message.follow_up.callback_number}."
                ),
            }]
        }
        sent = infrai.sms.batch.send(sms_payload, f"work-order:{message.work_order_id}:sms")
        message_id = str(sent["message_id"])
        events = infrai.sms.events(message_id)
        event_rows = events if isinstance(events, list) else events.get("events", [])
        follow_up = needs_technician_follow_up(event_rows)
        metric_payload = {
            "type": "counter",
            "name": "fieldservice.sms.follow_up_required",
            "value": 1 if follow_up else 0,
            "tags": {"work_order_id": message.work_order_id, "message_id": message_id},
        }
        infrai.metrics.report(metric_payload, f"work-order:{message.work_order_id}:metric")
        if follow_up:
            return DeliveryDecision(message.work_order_id, message_id, "contact_technician", "no delivered event")
        return DeliveryDecision(message.work_order_id, message_id, "wait_for_delivery", "delivered event recorded")
