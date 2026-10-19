from uuid import UUID

from app.rag.exceptions import RagConfigurationError, RagMetadataError


def require_user_id(user_id: UUID | None) -> UUID:
    if not isinstance(user_id, UUID) or user_id.int == 0:
        raise RagConfigurationError(
            "An authenticated user ID is required for project retrieval"
        )
    return user_id


def validate_project_metadata(
    *,
    authenticated_user_id: UUID,
    project_user_id: UUID,
    project_id: UUID,
    source_id: UUID,
    document_type: str,
) -> None:
    require_user_id(authenticated_user_id)
    if project_user_id != authenticated_user_id:
        raise RagMetadataError("Project ownership metadata is inconsistent")
    if source_id != project_id or document_type != "user_project":
        raise RagMetadataError("Project source metadata is inconsistent")
