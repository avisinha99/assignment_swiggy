from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.workflow_status import WorkflowStatus
from app.models.workflow_transition import WorkflowTransition
from app.schemas.project import ProjectCreate, ProjectOut

router = APIRouter()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    key = payload.key.strip().upper()
    existing = await db.scalar(select(Project).where(Project.key == key))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project key already exists")

    project = Project(key=key, name=payload.name.strip())
    db.add(project)
    await db.flush()

    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role="admin"))

    # default workflow
    statuses = [
        ("to_do", 0),
        ("in_progress", 1),
        ("in_review", 2),
        ("done", 3),
    ]
    for name, idx in statuses:
        db.add(WorkflowStatus(project_id=project.id, name=name, order_index=idx))
    transitions = [
        ("to_do", "in_progress"),
        ("in_progress", "in_review"),
        ("in_review", "done"),
        ("in_review", "in_progress"),
        ("in_progress", "to_do"),
    ]
    for f, t in transitions:
        db.add(WorkflowTransition(project_id=project.id, from_status=f, to_status=t))

    await db.commit()
    await db.refresh(project)
    return ProjectOut.model_validate(project, from_attributes=True)


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectOut]:
    projects = (
        await db.scalars(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == current_user.id)
            .order_by(Project.created_at.desc())
        )
    ).all()
    return [ProjectOut.model_validate(p, from_attributes=True) for p in projects]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    # simple membership guard
    project = await db.scalar(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(Project.id == project_id, ProjectMember.user_id == current_user.id)
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectOut.model_validate(project, from_attributes=True)
