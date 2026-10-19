from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.generate_ideas.ideas_service import load_stage1_context
from app.rag import embeddings
from app.rag.exceptions import RagConfigurationError, RagEmbeddingError, RagMetadataError
from app.rag.metadata import require_user_id, validate_project_metadata
from app.rag.vector_store import build_user_project_query


def test_project_retrieval_filters_ownership_before_similarity_limit():
    user_id = uuid4()
    statement = build_user_project_query(
        user_id,
        [0.0] * 768,
        top_k=4,
    )
    sql = str(statement.compile(dialect=postgresql.dialect()))
    normalized_sql = sql.upper()
    where_clause = normalized_sql.split("WHERE", maxsplit=1)[1].split(
        "ORDER BY", maxsplit=1
    )[0]

    assert "PROJECT_DOCUMENT_CHUNKS.USER_ID =" in where_clause
    assert "PROJECTS.USER_ID =" in where_clause
    assert "PROJECT_DOCUMENT_CHUNKS.DOCUMENT_TYPE =" in where_clause
    assert "PROJECTS.INDEXING_STATUS =" in where_clause
    assert "LIMIT" in normalized_sql


def test_missing_authenticated_identity_fails_closed():
    with pytest.raises(RagConfigurationError):
        require_user_id(None)
    with pytest.raises(RagConfigurationError):
        require_user_id(UUID(int=0))


def test_project_metadata_must_match_authenticated_owner():
    with pytest.raises(RagMetadataError):
        validate_project_metadata(
            authenticated_user_id=uuid4(),
            project_user_id=uuid4(),
            project_id=uuid4(),
            source_id=uuid4(),
            document_type="user_project",
        )


def test_embedding_provider_failure_is_reported(monkeypatch):
    def raise_provider_error(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        embeddings.client.models,
        "embed_content",
        raise_provider_error,
    )

    with pytest.raises(RagEmbeddingError):
        embeddings.embed_texts(["query"])


def test_landscape_analysis_access_is_scoped_to_authenticated_chat_owner():
    statement_holder = {}

    class EmptyDB:
        def scalar(self, statement):
            statement_holder["statement"] = statement
            return None

    authenticated_user = SimpleNamespace(
        id=uuid4(),
        user_name="owner",
    )
    with pytest.raises(PermissionError):
        load_stage1_context(
            EmptyDB(),
            uuid4(),
            authenticated_user,
        )

    sql = str(
        statement_holder["statement"].compile(
            dialect=postgresql.dialect()
        )
    )
    assert "chat.user_name =" in sql.lower()
    assert "landscape_analyses.id =" in sql.lower()
