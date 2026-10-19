from uuid import UUID

from sqlalchemy.orm import Session

from app.rag.config import settings
from app.rag.embeddings import embed_texts
from app.rag.metadata import require_user_id, validate_project_metadata
from app.rag.schemas import ProjectRetrievalResult, RetrievedProject
from app.rag.vector_store import search_user_project_chunks


def retrieve_user_projects(
    db: Session,
    authenticated_user_id: UUID,
    query: str,
    top_k: int | None = None,
) -> ProjectRetrievalResult:
    user_id = require_user_id(authenticated_user_id)
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("A non-empty project retrieval query is required")

    query_vector = embed_texts([normalized_query])[0]
    rows = search_user_project_chunks(
        db,
        user_id,
        query_vector,
        top_k or settings.retrieval_limit,
    )
    projects: list[RetrievedProject] = []
    seen: set[UUID] = set()
    for chunk, project, distance in rows:
        validate_project_metadata(
            authenticated_user_id=user_id,
            project_user_id=project.user_id,
            project_id=project.id,
            source_id=chunk.source_id,
            document_type=chunk.document_type,
        )
        score = 1.0 - float(distance)
        if score < settings.similarity_threshold or project.id in seen:
            continue
        seen.add(project.id)
        projects.append(
            RetrievedProject(
                project_id=project.id,
                name=project.name,
                excerpt=chunk.content,
                relevance_score=score,
                technologies=project.technologies or [],
                status=project.status,
                goals=project.goals or [],
                capabilities=project.capabilities or [],
                limitations=project.limitations or [],
            )
        )
    return ProjectRetrievalResult(
        projects=projects,
        project_ids=[item.project_id for item in projects],
    )
