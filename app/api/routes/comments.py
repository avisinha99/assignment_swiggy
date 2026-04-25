from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.comment import Comment
from app.models.issue import Issue
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentOut
from app.services.activity import log_activity
from app.services.notifications import notify_mentions

router = APIRouter()


@router.get("/issues/{issue_id}/comments", response_model=list[CommentOut])
async def list_comments(
    issue_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CommentOut]:
    issue = await db.scalar(select(Issue).where(Issue.id == issue_id))
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    member = await db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == issue.project_id, ProjectMember.user_id == user.id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")

    rows = (await db.scalars(select(Comment).where(Comment.issue_id == issue.id).order_by(Comment.id.asc()))).all()
    return [CommentOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/issues/{issue_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    issue_id: uuid.UUID,
    payload: CommentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentOut:
    issue = await db.scalar(select(Issue).where(Issue.id == issue_id))
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    member = await db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == issue.project_id, ProjectMember.user_id == user.id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")

    if payload.parent_comment_id is not None:
        parent = await db.scalar(select(Comment).where(Comment.id == payload.parent_comment_id, Comment.issue_id == issue.id))
        if not parent:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parent comment not found")

    c = Comment(
        issue_id=issue.id,
        author_id=user.id,
        parent_comment_id=payload.parent_comment_id,
        body=payload.body,
    )
    db.add(c)
    await db.flush()

    await notify_mentions(
        db,
        body=payload.body,
        payload={"issue_id": str(issue.id), "issue_key": issue.issue_key, "comment_id": c.id},
    )
    await log_activity(
        db,
        project_id=issue.project_id,
        actor_id=user.id,
        issue_id=issue.id,
        event_type="comment_added",
        payload={"issue_key": issue.issue_key, "comment_id": c.id},
    )

    await db.commit()
    await db.refresh(c)
    return CommentOut.model_validate(c, from_attributes=True)

