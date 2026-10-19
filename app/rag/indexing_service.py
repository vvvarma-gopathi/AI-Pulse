import logging
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.projects import Project, ProjectDocumentChunk
from app.rag.chunker import chunk_text
from app.rag.embeddings import embed_texts
from app.rag.metadata import validate_project_metadata

logger = logging.getLogger(__name__)


def project_document(project: Project) -> str:
    return "\n".join(
        (
            f"Project: {project.name}",
            f"Description: {project.description}",
            f"Technologies and frameworks: {', '.join(project.technologies or [])}",
            f"Goals: {', '.join(project.goals or [])}",
            f"Implemented capabilities: {', '.join(project.capabilities or [])}",
            f"Limitations: {', '.join(project.limitations or [])}",
            f"Status: {project.status}",
        )
    )


def index_project(db: Session, project: Project) -> int:
    validate_project_metadata(
        authenticated_user_id=project.user_id,
        project_user_id=project.user_id,
        project_id=project.id,
        source_id=project.id,
        document_type="user_project",
    )
    content_chunks = chunk_text(project_document(project))
    vectors = embed_texts(content_chunks)
    try:
        db.execute(
            delete(ProjectDocumentChunk).where(
                ProjectDocumentChunk.project_id == project.id,
                ProjectDocumentChunk.user_id == project.user_id,
            )
        )
        for index, (content, vector) in enumerate(
            zip(content_chunks, vectors, strict=True)
        ):
            chunk_id = uuid5(
                NAMESPACE_URL,
                f"aipulse:{project.user_id}:{project.id}:{index}",
            )
            db.add(
                ProjectDocumentChunk(
                    id=chunk_id,
                    user_id=project.user_id,
                    project_id=project.id,
                    document_type="user_project",
                    source_id=project.id,
                    chunk_index=index,
                    content=content,
                    embedding=vector,
                    updated_at=project.updated_at,
                )
            )
        project.indexing_status = "indexed"
        db.commit()
        return len(content_chunks)
    except Exception:
        db.rollback()
        logger.exception("Failed to index project %s", project.id)
        raise


def index_project_background(project_id: UUID, user_id: UUID) -> None:
    from core.database import SessionLocal

    db = SessionLocal()
    try:
        project = db.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )
        if project is None:
            return
        try:
            index_project(db, project)
        except Exception:
            logger.exception(
                "Project indexing failed for authenticated project %s",
                project_id,
            )
            db.rollback()
            project = db.scalar(
                select(Project).where(
                    Project.id == project_id,
                    Project.user_id == user_id,
                )
            )
            if project is not None:
                project.indexing_status = "failed"
                db.commit()
    except Exception:
        logger.exception(
            "Project indexing task failed for project %s",
            project_id,
        )
        raise
    finally:
        db.close()


def delete_project_chunks(
    db: Session,
    project_id: UUID,
    authenticated_user_id: UUID,
) -> None:
    db.execute(
        delete(ProjectDocumentChunk).where(
            ProjectDocumentChunk.project_id == project_id,
            ProjectDocumentChunk.user_id == authenticated_user_id,
        )
    )
