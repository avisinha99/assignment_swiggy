from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.issue import Issue
from app.models.issue_watcher import IssueWatcher
from app.models.project_member import ProjectMember
from app.models.user import User

router = APIRouter()


@router.post("/issues/{issue_id}/watch", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def watch_issue(
    issue_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    issue = await db.scalar(select(Issue).where(Issue.id == issue_id))
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    member = await db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == issue.project_id, ProjectMember.user_id == user.id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")

    existing = await db.scalar(select(IssueWatcher).where(IssueWatcher.issue_id == issue.id, IssueWatcher.user_id == user.id))
    if not existing:
        db.add(IssueWatcher(issue_id=issue.id, user_id=user.id))
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/issues/{issue_id}/unwatch", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def unwatch_issue(
    issue_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    issue = await db.scalar(select(Issue).where(Issue.id == issue_id))
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    await db.execute(delete(IssueWatcher).where(IssueWatcher.issue_id == issue.id, IssueWatcher.user_id == user.id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

