import asyncio
from uuid import UUID

from sqlalchemy.orm import Session

from app.rag.context_builder import build_project_context
from app.rag.config import settings
from app.rag.embeddings import embed_texts
from app.rag.metadata import require_user_id, validate_project_metadata
from app.rag.schemas import ProjectRetrievalResult, RetrievedProject
from app.rag.vector_store import search_user_project_chunks


def retrieve_project_context_with_embedding(
    db: Session,
    authenticated_user_id: UUID,
    query_embedding: list[float],
    top_k: int | None = None,
) -> tuple[list[dict], list[UUID]]:
    user_id = require_user_id(authenticated_user_id)
    rows = search_user_project_chunks(
        db,
        user_id,
        query_embedding,
        top_k or settings.retrieval_limit,
    )
    projects: list[RetrievedProject] = []
    seen: set[UUID] = set()
    remaining = settings.max_context_characters
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
        excerpt = chunk.content[:remaining]
        if not excerpt:
            break
        seen.add(project.id)
        projects.append(
            RetrievedProject(
                project_id=project.id,
                name=project.name,
                excerpt=excerpt,
                relevance_score=score,
                technologies=project.technologies or [],
                status=project.status,
                goals=project.goals or [],
                capabilities=project.capabilities or [],
                limitations=project.limitations or [],
            )
        )
        remaining -= len(excerpt)
        if remaining <= 0:
            break
    result = ProjectRetrievalResult(
        projects=projects,
        project_ids=[item.project_id for item in projects],
    )
    return build_project_context(result), result.project_ids


def retrieve_project_context(
    db: Session,
    authenticated_user_id: UUID,
    query: str,
    top_k: int | None = None,
) -> tuple[list[dict], list[UUID]]:
    user_id = require_user_id(authenticated_user_id)
    query_embedding = embed_texts([query.strip()])[0]
    return retrieve_project_context_with_embedding(
        db,
        user_id,
        query_embedding,
        top_k,
    )


async def retrieve_project_context_async(
    db: Session,
    authenticated_user_id: UUID,
    query: str,
    top_k: int | None = None,
) -> tuple[list[dict], list[UUID]]:
    user_id = require_user_id(authenticated_user_id)
    if not query.strip():
        raise ValueError("A non-empty project retrieval query is required")
    query_embedding = (
        await asyncio.to_thread(embed_texts, [query.strip()])
    )[0]
    return retrieve_project_context_with_embedding(
        db,
        user_id,
        query_embedding,
        top_k,
    )
