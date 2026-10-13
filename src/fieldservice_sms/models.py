from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class WorkOrderPhoto:
    photo_reference: str
    captured_at: str


@dataclass(frozen=True)
class DispatchStatus:
    state: Literal["dispatched", "en_route", "on_site"]
    updated_at: str


@dataclass(frozen=True)
class TechnicianFollowUp:
    technician_name: str
    callback_number: str


@dataclass(frozen=True)
class WorkOrderMessage:
    work_order_id: str
    recipient: str
    photo: WorkOrderPhoto
    dispatch: DispatchStatus
    follow_up: TechnicianFollowUp


@dataclass(frozen=True)
class DeliveryDecision:
    work_order_id: str
    message_id: str
    action: Literal["wait_for_delivery", "contact_technician"]
    reason: str
