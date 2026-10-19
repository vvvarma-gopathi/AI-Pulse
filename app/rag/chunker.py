from app.rag.config import settings


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    size = chunk_size or settings.chunk_size
    chunk_overlap = (
        settings.chunk_overlap if overlap is None else overlap
    )
    if size < 1 or chunk_overlap < 0 or chunk_overlap >= size:
        raise ValueError("Chunk size and overlap are invalid")

    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks = []
    start = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks
