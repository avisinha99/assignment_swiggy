from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.deps_project import get_project, require_project_member
from app.db.session import get_db
from app.models.issue import Issue
from app.models.issue_label import IssueLabel
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.issue import BoardColumn, BoardState, IssueCreate, IssueOut, IssuePatch
from app.services.activity import log_activity

router = APIRouter()


def _normalize_label(label: str) -> str:
    l = re.sub(r"\s+", "-", label.strip().lower())
    l = re.sub(r"[^a-z0-9_-]", "", l)
    return l[:50]


def _validate_parent_child(child_type: str, parent_type: str) -> bool:
    allowed = {
        "story": {"epic"},
        "sub_task": {"story"},
    }
    if child_type in allowed:
        return parent_type in allowed[child_type]
    return False


async def _next_issue_key(db: AsyncSession, project: Project) -> str:
    prefix = f"{project.key}-"
    last = await db.scalar(
        select(Issue.issue_key)
        .where(Issue.project_id == project.id, Issue.issue_key.like(f"{prefix}%"))
        .order_by(func.length(Issue.issue_key).desc(), Issue.issue_key.desc())
        .limit(1)
    )
    if not last:
        return f"{project.key}-1"
    try:
        n = int(last.split("-", 1)[1])
    except Exception:
        n = 0
    return f"{project.key}-{n+1}"


@router.post("/projects/{project_id}/issues", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
async def create_issue(
    payload: IssueCreate,
    project: Project = Depends(get_project),
    _member: ProjectMember = Depends(require_project_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IssueOut:
    parent_id = payload.parent_id
    if parent_id:
        parent = await db.scalar(select(Issue).where(Issue.id == parent_id, Issue.project_id == project.id))
        if not parent:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parent issue not found")
        if not _validate_parent_child(payload.type, parent.type):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid parent type: {payload.type} cannot be under {parent.type}",
            )

    issue_key = await _next_issue_key(db, project)
    issue = Issue(
        project_id=project.id,
        issue_key=issue_key,
        type=payload.type,
        title=payload.title.strip(),
        description=payload.description,
        status="to_do",
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        reporter_id=current_user.id,
        sprint_id=payload.sprint_id,
        story_points=payload.story_points,
        parent_id=payload.parent_id,
    )
    db.add(issue)
    await db.flush()

    for raw in payload.labels:
        lbl = _normalize_label(raw)
        if lbl:
            db.add(IssueLabel(issue_id=issue.id, label=lbl))

    await log_activity(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        issue_id=issue.id,
        event_type="issue_created",
        payload={"issue_key": issue.issue_key, "type": issue.type, "title": issue.title},
    )
    await db.commit()
    await db.refresh(issue)
    return IssueOut.model_validate(issue, from_attributes=True)


@router.patch("/issues/{issue_id}", response_model=IssueOut)
async def patch_issue(
    issue_id: uuid.UUID,
    payload: IssuePatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IssueOut:
    issue = await db.scalar(select(Issue).where(Issue.id == issue_id))
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    member = await db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == issue.project_id, ProjectMember.user_id == current_user.id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")

    if payload.expected_version is not None and payload.expected_version != issue.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Version conflict", "current_version": issue.version},
        )

    old_assignee = issue.assignee_id
    if payload.title is not None:
        issue.title = payload.title.strip()
    if payload.description is not None:
        issue.description = payload.description
    if payload.priority is not None:
        issue.priority = payload.priority
    if payload.status is not None:
        issue.status = payload.status
    if payload.assignee_id is not None or payload.assignee_id is None:
        issue.assignee_id = payload.assignee_id
    if payload.sprint_id is not None or payload.sprint_id is None:
        issue.sprint_id = payload.sprint_id
    if payload.story_points is not None or payload.story_points is None:
        issue.story_points = payload.story_points
    if payload.parent_id is not None:
        if payload.parent_id:
            parent = await db.scalar(
                select(Issue).where(Issue.id == payload.parent_id, Issue.project_id == issue.project_id)
            )
            if not parent:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parent issue not found")
            if not _validate_parent_child(issue.type, parent.type):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid parent type")
        issue.parent_id = payload.parent_id

    issue.version += 1

    # notify assignment changes (best-effort)
    if payload.assignee_id is not None and payload.assignee_id != old_assignee:
        from app.services.notifications import notify

        await notify(
            db,
            user_id=payload.assignee_id,
            type="assignment",
            payload={"issue_id": str(issue.id), "issue_key": issue.issue_key},
        )

    if payload.labels is not None:
        await db.execute(delete(IssueLabel).where(IssueLabel.issue_id == issue.id))
        for raw in payload.labels:
            lbl = _normalize_label(raw)
            if lbl:
                db.add(IssueLabel(issue_id=issue.id, label=lbl))

    await log_activity(
        db,
        project_id=issue.project_id,
        actor_id=current_user.id,
        issue_id=issue.id,
        event_type="issue_updated",
        payload={"issue_key": issue.issue_key, "version": issue.version},
    )
    await db.commit()
    await db.refresh(issue)
    return IssueOut.model_validate(issue, from_attributes=True)


@router.get("/projects/{project_id}/board", response_model=BoardState)
async def board_state(
    project: Project = Depends(get_project),
    _member: ProjectMember = Depends(require_project_member),
    db: AsyncSession = Depends(get_db),
) -> BoardState:
    issues = (await db.scalars(select(Issue).where(Issue.project_id == project.id).order_by(Issue.created_at.desc()))).all()
    by_status: dict[str, list[Issue]] = {}
    for i in issues:
        by_status.setdefault(i.status, []).append(i)

    columns = [BoardColumn(status=s, issues=[IssueOut.model_validate(x, from_attributes=True) for x in xs]) for s, xs in by_status.items()]
    columns.sort(key=lambda c: c.status)
    return BoardState(project_id=project.id, columns=columns)
