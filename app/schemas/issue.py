import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class IssueCreate(BaseModel):
    type: str = Field(pattern=r"^(epic|story|task|bug|sub_task)$")
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    priority: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    assignee_id: uuid.UUID | None = None
    sprint_id: uuid.UUID | None = None
    story_points: int | None = Field(default=None, ge=0, le=1000)
    parent_id: uuid.UUID | None = None
    labels: list[str] = Field(default_factory=list)


class IssuePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    priority: str | None = Field(default=None, pattern=r"^(low|medium|high|critical)$")
    status: str | None = None
    assignee_id: uuid.UUID | None = None
    sprint_id: uuid.UUID | None = None
    story_points: int | None = Field(default=None, ge=0, le=1000)
    parent_id: uuid.UUID | None = None
    labels: list[str] | None = None
    expected_version: int | None = None


class IssueOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    issue_key: str
    type: str
    title: str
    description: str | None
    status: str
    priority: str
    assignee_id: uuid.UUID | None
    reporter_id: uuid.UUID
    sprint_id: uuid.UUID | None
    story_points: int | None
    parent_id: uuid.UUID | None
    version: int
    created_at: datetime
    updated_at: datetime


class BoardColumn(BaseModel):
    status: str
    issues: list[IssueOut]


class BoardState(BaseModel):
    project_id: uuid.UUID
    columns: list[BoardColumn]
