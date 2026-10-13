from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .dispatch_followup import DispatchMessenger
from .infrai import InfraiClient, InfraiError
from .models import DispatchStatus, TechnicianFollowUp, WorkOrderMessage, WorkOrderPhoto


class PhotoInput(BaseModel):
    photo_reference: str = Field(min_length=1)
    captured_at: str


class DispatchInput(BaseModel):
    state: str
    updated_at: str


class FollowUpInput(BaseModel):
    technician_name: str
    callback_number: str


class WorkOrderInput(BaseModel):
    work_order_id: str
    recipient: str
    photo: PhotoInput
    dispatch: DispatchInput
    follow_up: FollowUpInput


app = FastAPI(title="Field-service SMS delivery trace")


@app.post("/work-orders/dispatch-message")
def dispatch_message(payload: WorkOrderInput) -> dict[str, str]:
    work_order = WorkOrderMessage(
        work_order_id=payload.work_order_id,
        recipient=payload.recipient,
        photo=WorkOrderPhoto(**payload.photo.model_dump()),
        dispatch=DispatchStatus(**payload.dispatch.model_dump()),
        follow_up=TechnicianFollowUp(**payload.follow_up.model_dump()),
    )
    try:
        decision = DispatchMessenger(InfraiClient()).send_and_assess(work_order)
    except InfraiError as error:
        raise HTTPException(status_code=400, detail={"code": error.code}) from error
    return {
        "work_order_id": decision.work_order_id,
        "message_id": decision.message_id,
        "action": decision.action,
        "reason": decision.reason,
    }
