from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.auth_model import Users
from app.models.projects import Project
from app.rag.indexing_service import (
    delete_project_chunks,
    index_project_background,
)
from app.schemas.projects import ProjectResponse, ProjectWrite
from app.services.auth_services import get_current_user

projects_router = APIRouter(prefix="/projects", tags=["Projects"])


@projects_router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project_data: ProjectWrite,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        user_id=user.id,
        **project_data.model_dump(),
        indexing_status="pending",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    background_tasks.add_task(
        index_project_background,
        project.id,
        user.id,
    )
    return project


@projects_router.get("", response_model=list[ProjectResponse])
def list_projects(
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.updated_at.desc())
    ).all()


@projects_router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@projects_router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project_data: ProjectWrite,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in project_data.model_dump().items():
        setattr(project, field, value)
    project.updated_at = datetime.now(timezone.utc)
    project.indexing_status = "pending"
    db.commit()
    db.refresh(project)
    background_tasks.add_task(
        index_project_background,
        project.id,
        user.id,
    )
    return project


@projects_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    delete_project_chunks(db, project.id, user.id)
    db.delete(project)
    db.commit()


@projects_router.post(
    "/{project_id}/reindex",
    response_model=ProjectResponse,
)
def reindex_project(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.indexing_status = "pending"
    db.commit()
    db.refresh(project)
    background_tasks.add_task(
        index_project_background,
        project.id,
        user.id,
    )
    return project
