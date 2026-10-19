import os

from pgvector.sqlalchemy import VECTOR


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


class RagSettings:
    embedding_model = os.getenv(
        "RAG_EMBEDDING_MODEL",
        "gemini-embedding-001",
    )
    embedding_dimensions = _positive_int(
        "RAG_EMBEDDING_DIMENSIONS",
        768,
    )
    similarity_threshold = float(
        os.getenv("RAG_SIMILARITY_THRESHOLD", "0.25")
    )
    retrieval_limit = _positive_int("RAG_RETRIEVAL_LIMIT", 5)
    max_context_characters = _positive_int(
        "RAG_MAX_CONTEXT_CHARACTERS",
        12000,
    )
    chunk_size = _positive_int("RAG_CHUNK_SIZE", 1500)
    chunk_overlap = _positive_int("RAG_CHUNK_OVERLAP", 150)

    def __init__(self):
        if not 0.0 <= self.similarity_threshold <= 1.0:
            raise ValueError(
                "RAG_SIMILARITY_THRESHOLD must be between 0 and 1"
            )

    @property
    def vector_type(self) -> VECTOR:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "RAG_CHUNK_OVERLAP must be less than RAG_CHUNK_SIZE"
            )
        return VECTOR(self.embedding_dimensions)


settings = RagSettings()
