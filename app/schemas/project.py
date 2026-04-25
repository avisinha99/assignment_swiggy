import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    key: str = Field(min_length=2, max_length=20, pattern=r"^[A-Z][A-Z0-9]+$")
    name: str = Field(min_length=1, max_length=200)


class ProjectOut(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    created_at: datetime
