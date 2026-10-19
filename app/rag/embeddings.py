import math

from google.genai import types

from app.LLM.llm import client
from app.rag.config import settings
from app.rag.exceptions import RagEmbeddingError


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    try:
        response = client.models.embed_content(
            model=settings.embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.embedding_dimensions,
            ),
        )
    except Exception as exc:
        raise RagEmbeddingError("Embedding provider request failed") from exc

    embeddings = getattr(response, "embeddings", None) or []
    vectors = [list(item.values or []) for item in embeddings]
    if len(vectors) != len(texts):
        raise RagEmbeddingError(
            "Embedding provider returned an unexpected vector count"
        )
    for vector in vectors:
        if len(vector) != settings.embedding_dimensions:
            raise RagEmbeddingError(
                "Embedding provider returned an unexpected vector size"
            )
        if not all(math.isfinite(value) for value in vector):
            raise RagEmbeddingError(
                "Embedding provider returned a non-finite vector value"
            )
    return vectors
