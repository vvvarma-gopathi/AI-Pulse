from datetime import datetime
from uuid import UUID

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.blog_schemas import HomepageArticleResponse


class ChatDiscoveredProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    article_summary_id: UUID
    name: str
    candidate_url: str
    description: str | None
    search_query: str
    evidence_status: str
    discovered_at: datetime


class LandscapeAnalysisHistory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_name: str
    prompt_version: str
    analysis: dict[str, Any]
    created_at: datetime


class GeneratedIdeaHistory(BaseModel):
    id: UUID
    title: str
    problem: str
    feasibility_score: int
    potential_impact_score: int
    novelty_score: int
    details: dict[str, Any]
    created_at: datetime


class IdeaGenerationHistory(BaseModel):
    id: UUID
    landscape_analysis_id: UUID
    generation_mode: str
    status: str
    retrieval_status: str
    overall_summary: str
    created_at: datetime
    ideas: list[GeneratedIdeaHistory]


class ChatAnalysisResponse(BaseModel):
    chat_id: UUID
    articles: list[HomepageArticleResponse]
    discovered_products: list[ChatDiscoveredProduct]
    landscape_analyses: list[LandscapeAnalysisHistory]
    idea_generations: list[IdeaGenerationHistory]


class ChatHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
