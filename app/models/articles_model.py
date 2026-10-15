from sqlalchemy import ForeignKey
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UniqueConstraint
from core.database import Base


class Chat(Base):
    __tablename__='chat'
    id:Mapped[UUID]=mapped_column(PG_UUID(as_uuid=True),primary_key=True,default=uuid4)
    user_name:Mapped[str]=mapped_column(String(225),unique=False,nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    title:Mapped[str]=mapped_column(String(500),nullable=False)

class ArticleSummary(Base):
    __tablename__ = "article_summaries"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        unique=True,
        index=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    technologies: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    chat_id: Mapped[UUID] = mapped_column(
    PG_UUID(as_uuid=True),ForeignKey(Chat.id,ondelete="CASCADE"),
    nullable=False,
    index=True,
    )



class DiscoveredProduct(Base):
    __tablename__ = "discovered_products"

    __table_args__ = (
        UniqueConstraint(
            "article_summary_id",
            "candidate_url",
            name="uq_discovered_article_candidate",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    article_summary_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("article_summaries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    candidate_url: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    search_query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    chat_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    evidence_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="unverified",
    )

    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
