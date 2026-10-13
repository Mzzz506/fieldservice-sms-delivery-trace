from fieldservice_sms.dispatch_followup import needs_technician_follow_up


def test_missing_delivery_event_requires_technician_follow_up() -> None:
    events = [{"status": "queued"}, {"status": "sent"}]

    assert needs_technician_follow_up(events) is True
