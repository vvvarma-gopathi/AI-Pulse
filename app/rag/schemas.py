from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectTextChunk(BaseModel):
    project_id: UUID
    user_id: UUID
    document_type: str = "user_project"
    source_id: UUID
    chunk_index: int = Field(ge=0)
    updated_at: datetime
    content: str = Field(min_length=1)


class RetrievedProject(BaseModel):
    project_id: UUID
    name: str
    excerpt: str
    relevance_score: float
    technologies: list[str]
    status: str
    goals: list[str]
    capabilities: list[str]
    limitations: list[str]


class ProjectRetrievalResult(BaseModel):
    projects: list[RetrievedProject]
    project_ids: list[UUID]
