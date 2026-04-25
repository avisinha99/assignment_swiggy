from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.deps_project import get_project, require_project_member
from app.db.session import get_db
from app.models.issue import Issue
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.sprint import Sprint
from app.models.user import User
from app.schemas.sprint import SprintCompleteRequest, SprintCompleteResponse, SprintCreate, SprintOut

router = APIRouter()


@router.get("/projects/{project_id}/sprints", response_model=list[SprintOut])
async def list_sprints(
    project: Project = Depends(get_project),
    _member: ProjectMember = Depends(require_project_member),
    db: AsyncSession = Depends(get_db),
) -> list[SprintOut]:
    rows = (await db.scalars(select(Sprint).where(Sprint.project_id == project.id).order_by(Sprint.created_at.desc()))).all()
    return [SprintOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/projects/{project_id}/sprints", response_model=SprintOut, status_code=status.HTTP_201_CREATED)
async def create_sprint(
    payload: SprintCreate,
    project: Project = Depends(get_project),
    _member: ProjectMember = Depends(require_project_member),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SprintOut:
    sprint = Sprint(
        project_id=project.id,
        name=payload.name.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date,
        state="planned",
    )
    db.add(sprint)
    await db.commit()
    await db.refresh(sprint)
    return SprintOut.model_validate(sprint, from_attributes=True)


@router.post("/sprints/{sprint_id}/start", response_model=SprintOut)
async def start_sprint(
    sprint_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SprintOut:
    sprint = await db.scalar(select(Sprint).where(Sprint.id == sprint_id))
    if not sprint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")

    member = await db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == sprint.project_id, ProjectMember.user_id == user.id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")

    sprint.state = "active"
    await db.commit()
    await db.refresh(sprint)
    return SprintOut.model_validate(sprint, from_attributes=True)


@router.post("/sprints/{sprint_id}/complete", response_model=SprintCompleteResponse)
async def complete_sprint(
    sprint_id: uuid.UUID,
    payload: SprintCompleteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SprintCompleteResponse:
    sprint = await db.scalar(select(Sprint).where(Sprint.id == sprint_id))
    if not sprint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")

    member = await db.scalar(
        select(ProjectMember).where(ProjectMember.project_id == sprint.project_id, ProjectMember.user_id == user.id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")

    incomplete = (
        await db.scalars(
            select(Issue.id).where(Issue.sprint_id == sprint.id, Issue.status != "done")
        )
    ).all()
    incomplete_ids = [uuid.UUID(str(i)) for i in incomplete]

    completed_points = await db.scalar(
        select(func.coalesce(func.sum(Issue.story_points), 0)).where(Issue.sprint_id == sprint.id, Issue.status == "done")
    )
    completed_points_int = int(completed_points or 0)

    # carry-over
    if payload.carry_over_issue_ids:
        target = payload.carry_over_to_sprint_id
        if target is not None:
            target_sprint = await db.scalar(select(Sprint).where(Sprint.id == target, Sprint.project_id == sprint.project_id))
            if not target_sprint:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Target sprint not found")

        # move selected issues
        for iid in payload.carry_over_issue_ids:
            if iid not in incomplete_ids:
                continue
            issue = await db.scalar(select(Issue).where(Issue.id == iid, Issue.sprint_id == sprint.id))
            if issue:
                issue.sprint_id = target

    sprint.state = "completed"
    await db.commit()

    return SprintCompleteResponse(
        sprint_id=sprint.id,
        completed_story_points=completed_points_int,
        incomplete_issue_ids=incomplete_ids,
    )

