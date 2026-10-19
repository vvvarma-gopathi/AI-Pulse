from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


IdeaMode = Literal[
    "new_product",
    "project_improvement",
    "technology_combination",
]


class IdeaEvidence(BaseModel):
    article_id: str
    source_url: str
    explanation: str


class GeneratedIdea(BaseModel):
    title: str = Field(min_length=5, max_length=150)
    tagline: str = Field(max_length=250)

    problem: str
    target_users: list[str] = Field(min_length=1)
    proposed_solution: str

    core_features: list[str] = Field(min_length=1)
    technologies: list[str] = Field(default_factory=list)

    differentiation: str
    similar_products: list[str] = Field(default_factory=list)

    supporting_evidence: list[IdeaEvidence] = Field(min_length=1)
    personalization_rationale: str

    assumptions: list[str] = Field(default_factory=list)

    feasibility_score: int = Field(ge=1, le=10)
    potential_impact_score: int = Field(ge=1, le=10)
    novelty_score: int = Field(ge=1, le=10)

    score_rationale: str

    mvp_scope: list[str] = Field(min_length=1)
    validation_steps: list[str] = Field(min_length=1)


class IdeaGenerationResponse(BaseModel):
    research_analysis_id: str
    generation_mode: IdeaMode
    overall_summary: str
    ideas: list[GeneratedIdea] = Field(default_factory=list)


class IdeaGenerationRequest(BaseModel):
    request_id: UUID | None = None
    landscape_analysis_id: UUID
    mode: IdeaMode = "new_product"
    project_id: UUID | None = None

    number_of_ideas: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class IdeaGenerationAPIResponse(BaseModel):
    generation_id: str
    landscape_analysis_id: str
    chat_id: str
    model_name: str
    generation_mode: str
    overall_summary: str
    ideas: list[GeneratedIdea]
    created_at: str