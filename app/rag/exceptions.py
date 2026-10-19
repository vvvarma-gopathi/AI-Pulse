class RagError(RuntimeError):
    """Base exception for retrieval and indexing failures."""


class RagConfigurationError(RagError):
    """Raised when RAG configuration or identity is invalid."""


class RagEmbeddingError(RagError):
    """Raised when an embedding provider fails or returns bad data."""


class RagMetadataError(RagError):
    """Raised when stored ownership metadata is inconsistent."""
