import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IdeaGenerationRun(Base):
    __tablename__ = "idea_generation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    landscape_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "landscape_analyses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    generation_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    prompt_version: Mapped[str] = mapped_column(
        String(50),
        default="idea-generation-v1",
        nullable=False,
    )

    overall_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ProjectIdea(Base):
    __tablename__ = "project_ideas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    generation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "idea_generation_runs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    problem: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    feasibility_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    potential_impact_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    novelty_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Full validated idea, including evidence and MVP.
    details: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


Index(
    "ix_project_ideas_generation_title",
    ProjectIdea.generation_id,
    ProjectIdea.title,
)