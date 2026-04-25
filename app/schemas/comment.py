import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=20000)
    parent_comment_id: int | None = None


class CommentOut(BaseModel):
    id: int
    issue_id: uuid.UUID
    author_id: uuid.UUID
    parent_comment_id: int | None
    body: str
    created_at: datetime
