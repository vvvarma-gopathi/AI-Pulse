from uuid import UUID

from sqlalchemy import Select, select

from app.models.projects import Project, ProjectDocumentChunk
from app.rag.config import settings
from app.rag.metadata import require_user_id


def build_user_project_query(
    authenticated_user_id: UUID,
    query_embedding: list[float],
    top_k: int,
) -> Select:
    user_id = require_user_id(authenticated_user_id)
    if not query_embedding:
        raise ValueError("A query embedding is required")
    limit = max(1, min(top_k, settings.retrieval_limit))
    distance = ProjectDocumentChunk.embedding.cosine_distance(
        query_embedding
    )
    return (
        select(
            ProjectDocumentChunk,
            Project,
            distance.label("distance"),
        )
        .join(Project, Project.id == ProjectDocumentChunk.project_id)
        .where(
            ProjectDocumentChunk.user_id == user_id,
            Project.user_id == user_id,
            ProjectDocumentChunk.document_type == "user_project",
            ProjectDocumentChunk.source_id == Project.id,
            Project.indexing_status == "indexed",
            ProjectDocumentChunk.updated_at == Project.updated_at,
        )
        .order_by(distance)
        .limit(limit)
    )


def search_user_project_chunks(
    db,
    authenticated_user_id: UUID,
    query_embedding: list[float],
    top_k: int,
):
    statement = build_user_project_query(
        authenticated_user_id,
        query_embedding,
        top_k,
    )
    return db.execute(statement).all()
