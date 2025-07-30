from my_aws_helpers.event import Event, EventStatus
import pytest


def test_event():
    event = Event(status=EventStatus.success.value, message="test event")
    assert event != None

def test_event_wrong_status():
    with pytest.raises(Exception):
        Event(status="not success", message="test event")
        
