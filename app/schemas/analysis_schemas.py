from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    article_id: str
    source_url: str
    explanation: str


class TechnologyTrend(BaseModel):
    name: str
    description: str
    technologies: list[str] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    confidence: int = Field(ge=1, le=10)


class TechnicalCapability(BaseModel):
    name: str
    what_it_enables: str
    technologies: list[str] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)


class ProblemSignal(BaseModel):
    problem: str
    affected_users: list[str] = Field(default_factory=list)
    current_approaches: list[str] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    confidence: int = Field(ge=1, le=10)


class ProductLandscapeItem(BaseModel):
    product_name: str
    product_url: str
    described_capabilities: list[str] = Field(
        default_factory=list
    )
    technologies: list[str] = Field(default_factory=list)
    evidence_status: str = "unknown"
    source_article_ids: list[str] = Field(default_factory=list)


class PotentialGap(BaseModel):
    description: str
    supporting_signals: list[str] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    validation_needed: list[str] = Field(default_factory=list)
    confidence: int = Field(ge=1, le=10)


class TechnologyConnection(BaseModel):
    technologies: list[str] = Field(min_length=2)
    relationship: str
    possible_capability: str
    evidence: list[EvidenceReference] = Field(default_factory=list)


class LandscapeAnalysis(BaseModel):
    research_summary: str

    key_trends: list[TechnologyTrend] = Field(
        default_factory=list
    )

    emerging_capabilities: list[TechnicalCapability] = Field(
        default_factory=list
    )

    recurring_problems: list[ProblemSignal] = Field(
        default_factory=list
    )

    product_landscape: list[ProductLandscapeItem] = Field(
        default_factory=list
    )

    potential_gaps: list[PotentialGap] = Field(
        default_factory=list
    )

    technology_connections: list[TechnologyConnection] = Field(
        default_factory=list
    )

    research_limitations: list[str] = Field(
        default_factory=list
    )

    recommended_research_directions: list[str] = Field(
        default_factory=list
    )