import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class SprintCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None


class SprintOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    start_date: date | None
    end_date: date | None
    state: str
    created_at: datetime


class SprintCompleteRequest(BaseModel):
    carry_over_issue_ids: list[uuid.UUID] = Field(default_factory=list)
    carry_over_to_sprint_id: uuid.UUID | None = None


class SprintCompleteResponse(BaseModel):
    sprint_id: uuid.UUID
    completed_story_points: int
    incomplete_issue_ids: list[uuid.UUID]
