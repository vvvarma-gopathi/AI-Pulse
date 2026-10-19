from pydantic import BaseModel, ConfigDict
from pydantic import Field
from datetime import datetime
from uuid import UUID

class ArticleSummary(BaseModel):
    title:str
    summary:str
    url:str
    published_at:datetime
    technologies:list[str]

class ArticleSummaryResponse(BaseModel):
    articles: list[ArticleSummary]


class HomepageArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    summary: str
    url: str
    published_at: datetime | None
    technologies: list[str]
    created_at: datetime