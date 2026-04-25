import uuid
from datetime import datetime

from pydantic import BaseModel


class ActivityOut(BaseModel):
    id: int
    project_id: uuid.UUID
    issue_id: uuid.UUID | None
    actor_id: uuid.UUID
    event_type: str
    payload: str
    created_at: datetime


class ActivityPage(BaseModel):
    items: list[ActivityOut]
    next_cursor: int | None
