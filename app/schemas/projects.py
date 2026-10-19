from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ProjectText = Annotated[str, Field(min_length=1, max_length=500)]


class ProjectWrite(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=20_000)
    technologies: list[ProjectText] = Field(default_factory=list, max_length=50)
    goals: list[ProjectText] = Field(default_factory=list, max_length=50)
    capabilities: list[ProjectText] = Field(default_factory=list, max_length=50)
    limitations: list[ProjectText] = Field(default_factory=list, max_length=50)
    status: str = Field(default="active", max_length=50)


class ProjectResponse(ProjectWrite):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    indexing_status: str
    created_at: datetime
    updated_at: datetime
