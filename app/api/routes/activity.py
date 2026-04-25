from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.deps_project import get_project, require_project_member
from app.db.session import get_db
from app.models.activity import Activity
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.activity import ActivityOut, ActivityPage

router = APIRouter()


@router.get("/projects/{project_id}/activity", response_model=ActivityPage)
async def activity_feed(
    project: Project = Depends(get_project),
    _member: ProjectMember = Depends(require_project_member),
    _user: User = Depends(get_current_user),
    cursor: int | None = Query(default=None, description="Return items with id < cursor"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ActivityPage:
    q = select(Activity).where(Activity.project_id == project.id)
    if cursor is not None:
        q = q.where(Activity.id < cursor)
    q = q.order_by(Activity.id.desc()).limit(limit + 1)

    rows = (await db.scalars(q)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = rows[-1].id if has_more and rows else None
    return ActivityPage(
        items=[ActivityOut.model_validate(r, from_attributes=True) for r in rows],
        next_cursor=next_cursor,
    )

