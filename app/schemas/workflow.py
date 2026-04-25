import uuid
from pydantic import BaseModel, Field


class WorkflowStatusOut(BaseModel):
    id: uuid.UUID
    name: str
    order_index: int


class WorkflowStatusCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    order_index: int = 0


class WorkflowTransitionOut(BaseModel):
    id: uuid.UUID
    from_status: str
    to_status: str


class WorkflowTransitionCreate(BaseModel):
    from_status: str = Field(min_length=1, max_length=50)
    to_status: str = Field(min_length=1, max_length=50)


class TransitionRequest(BaseModel):
    to_status: str = Field(min_length=1, max_length=50)
    expected_version: int | None = None
