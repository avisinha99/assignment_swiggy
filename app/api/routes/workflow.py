from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.deps_project import get_project, require_project_admin, require_project_member
from app.db.session import get_db
from app.models.issue import Issue
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.workflow_status import WorkflowStatus
from app.models.workflow_transition import WorkflowTransition
from app.schemas.issue import IssueOut
from app.schemas.workflow import (
    TransitionRequest,
    WorkflowStatusCreate,
    WorkflowStatusOut,
    WorkflowTransitionCreate,
    WorkflowTransitionOut,
)
from app.services.activity import log_activity

router = APIRouter()


@router.get("/projects/{project_id}/workflow/statuses", response_model=list[WorkflowStatusOut])
async def list_statuses(
    project: Project = Depends(get_project),
    _member: ProjectMember = Depends(require_project_member),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowStatusOut]:
    rows = (await db.scalars(select(WorkflowStatus).where(WorkflowStatus.project_id == project.id).order_by(WorkflowStatus.order_index))).all()
    return [WorkflowStatusOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/projects/{project_id}/workflow/statuses", response_model=WorkflowStatusOut, status_code=status.HTTP_201_CREATED)
async def create_status(
    payload: WorkflowStatusCreate,
    project: Project = Depends(get_project),
    _admin: ProjectMember = Depends(require_project_admin),
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusOut:
    status_obj = WorkflowStatus(project_id=project.id, name=payload.name.strip(), order_index=payload.order_index)
    db.add(status_obj)
    await db.commit()
    await db.refresh(status_obj)
    return WorkflowStatusOut.model_validate(status_obj, from_attributes=True)


@router.get("/projects/{project_id}/workflow/transitions", response_model=list[WorkflowTransitionOut])
async def list_transitions(
    project: Project = Depends(get_project),
    _member: ProjectMember = Depends(require_project_member),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowTransitionOut]:
    rows = (
        await db.scalars(select(WorkflowTransition).where(WorkflowTransition.project_id == project.id))
    ).all()
    return [WorkflowTransitionOut.model_validate(r, from_attributes=True) for r in rows]


@router.post(
    "/projects/{project_id}/workflow/transitions",
    response_model=WorkflowTransitionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_transition(
    payload: WorkflowTransitionCreate,
    project: Project = Depends(get_project),
    _admin: ProjectMember = Depends(require_project_admin),
    db: AsyncSession = Depends(get_db),
) -> WorkflowTransitionOut:
    tr = WorkflowTransition(
        project_id=project.id,
        from_status=payload.from_status.strip(),
        to_status=payload.to_status.strip(),
    )
    db.add(tr)
    await db.commit()
    await db.refresh(tr)
    return WorkflowTransitionOut.model_validate(tr, from_attributes=True)


async def _allowed_to_statuses(db: AsyncSession, project_id: uuid.UUID, from_status: str) -> list[str]:
    tos = (
        await db.scalars(
            select(WorkflowTransition.to_status).where(
                WorkflowTransition.project_id == project_id,
                WorkflowTransition.from_status == from_status,
            )
        )
    ).all()
    return list(dict.fromkeys(tos))


@router.post("/issues/{issue_id}/transitions", response_model=IssueOut)
async def transition_issue(
    issue_id: uuid.UUID,
    payload: TransitionRequest,
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

    allowed = await _allowed_to_statuses(db, issue.project_id, issue.status)
    to_status = payload.to_status.strip()
    if to_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Transition not allowed", "from_status": issue.status, "allowed": allowed},
        )

    # Basic hook: when moving to in_review, auto-assign a reviewer if unassigned.
    if to_status == "in_review" and issue.assignee_id is None:
        # pick first project admin
        admin_user_id = await db.scalar(
            select(ProjectMember.user_id).where(
                ProjectMember.project_id == issue.project_id,
                ProjectMember.role == "admin",
            )
        )
        if admin_user_id:
            issue.assignee_id = admin_user_id

    from_status = issue.status
    issue.status = to_status
    issue.version += 1

    await log_activity(
        db,
        project_id=issue.project_id,
        actor_id=current_user.id,
        issue_id=issue.id,
        event_type="issue_moved",
        payload={"issue_key": issue.issue_key, "from": from_status, "to": to_status, "version": issue.version},
    )
    await db.commit()
    await db.refresh(issue)
    return IssueOut.model_validate(issue, from_attributes=True)

