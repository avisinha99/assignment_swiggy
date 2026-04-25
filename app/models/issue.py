import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.types import GUID


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    issue_key: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)  # e.g. PROJ-123

    type: Mapped[str] = mapped_column(String(20), nullable=False)  # epic|story|task|bug|sub_task
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="to_do")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    assignee_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)

    sprint_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("sprints.id"), nullable=True, index=True)

    story_points: Mapped[int | None] = mapped_column(Integer, nullable=True)

    parent_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("issues.id"), nullable=True, index=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # optimistic locking

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
