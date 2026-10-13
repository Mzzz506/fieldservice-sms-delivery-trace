import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fieldservice_sms.dispatch_followup import DispatchMessenger
from fieldservice_sms.infrai import InfraiClient
from fieldservice_sms.models import DispatchStatus, TechnicianFollowUp, WorkOrderMessage, WorkOrderPhoto


message = WorkOrderMessage(
    work_order_id="WO-2048",
    recipient=os.environ["FIELD_SERVICE_RECIPIENT"],
    photo=WorkOrderPhoto(photo_reference="photo-2048", captured_at="2026-09-15T09:00:00Z"),
    dispatch=DispatchStatus(state="en_route", updated_at="2026-09-15T09:05:00Z"),
    follow_up=TechnicianFollowUp(technician_name="Mina", callback_number="+15550190"),
)
decision = DispatchMessenger(InfraiClient()).send_and_assess(message)
print(f"{decision.message_id}: {decision.action} ({decision.reason})")
