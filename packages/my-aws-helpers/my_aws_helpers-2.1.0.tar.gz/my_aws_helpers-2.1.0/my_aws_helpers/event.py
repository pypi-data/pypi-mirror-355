from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4


class EventStatus(str, Enum):
    in_progress = "in_progress"
    success = "success"
    fail = "fail"


@dataclass
class Event:
    status: str
    message: str
    id: str
    created_timestamp: datetime

    def __init__(
        self,
        status: str,
        message: str,
        id: str = None,
        created_timestamp: datetime = None,
    ):
        self.status: str = self.set_status(status=status)
        self.message: str = message
        self.id: str = id if id else uuid4().hex
        self.created_timestamp: datetime = created_timestamp if created_timestamp else datetime.now()

    def set_status(self, status: str) -> str:
        if status not in list(EventStatus):
            raise Exception("Status must be a member of EventStatus")
        return status


