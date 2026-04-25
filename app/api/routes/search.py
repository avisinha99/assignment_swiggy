from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.issue import Issue
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.issue import IssueOut

router = APIRouter()


def _parse_cursor(cursor: str) -> tuple[datetime, str] | None:
    try:
        created_at_s, issue_id_s = cursor.split("|", 1)
        return datetime.fromisoformat(created_at_s.replace("Z", "+00:00")), issue_id_s
    except Exception:
        return None


@router.get("/search", response_model=dict)
async def search_issues(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assignee_id: uuid.UUID | None = Query(default=None),
    cursor: str | None = Query(default=None, description="Pagination cursor: created_at|issue_id"),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(Issue).join(ProjectMember, ProjectMember.project_id == Issue.project_id).where(ProjectMember.user_id == user.id)

    if status:
        stmt = stmt.where(Issue.status == status)
    if priority:
        stmt = stmt.where(Issue.priority == priority)
    if assignee_id is not None:
        stmt = stmt.where(Issue.assignee_id == assignee_id)

    if cursor:
        parsed = _parse_cursor(cursor)
        if parsed:
            ctime, cid = parsed
            stmt = stmt.where(or_(Issue.created_at < ctime, and_(Issue.created_at == ctime, Issue.id < cid)))

    stmt = stmt.order_by(Issue.created_at.desc(), Issue.id.desc()).limit(limit + 1)
    rows = (await db.scalars(stmt)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = f"{last.created_at.isoformat()}|{last.id}"

    return {
        "items": [IssueOut.model_validate(r, from_attributes=True) for r in rows],
        "next_cursor": next_cursor,
    }

