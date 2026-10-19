from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.chat_routes import view_chat_analysis
from app.models.articles_model import ArticleSummary, Chat, DiscoveredProduct
from app.models.analysis import LandscapeAnalysisRecord
from app.models.ideas import IdeaGenerationRun, ProjectIdea


class FakeDB:
    def __init__(self, chat, results):
        self.chat = chat
        self.results = results
        self.scalar_calls = 0
        self.scalar_queries = []
        self.scalars_queries = []

    def scalar(self, statement):
        self.scalar_calls += 1
        self.scalar_queries.append(statement)
        return self.chat

    def scalars(self, statement):
        self.scalars_queries.append(statement)
        entity = statement.column_descriptions[0]["entity"]
        return SimpleNamespace(all=lambda: self.results.get(entity, []))


def test_view_chat_analysis_returns_all_chat_related_research():
    now = datetime.now(timezone.utc)
    user = SimpleNamespace(id=uuid4(), user_name="alice")
    chat = SimpleNamespace(id=uuid4())
    article = SimpleNamespace(
        id=uuid4(),
        title="Research",
        summary="Summary",
        url="https://example.test/article",
        published_at=None,
        technologies=["Python"],
        created_at=now,
    )
    product = SimpleNamespace(
        id=uuid4(),
        article_summary_id=article.id,
        name="Open source app",
        candidate_url="https://example.test/app",
        description="An app",
        search_query="open source app",
        evidence_status="verified",
        discovered_at=now,
    )
    analysis = SimpleNamespace(
        id=uuid4(),
        model_name="model",
        prompt_version="v1",
        analysis={"research_summary": "Analysis"},
        created_at=now,
    )
    run = SimpleNamespace(
        id=uuid4(),
        landscape_analysis_id=analysis.id,
        generation_mode="new_product",
        status="completed",
        retrieval_status="completed",
        overall_summary="Idea summary",
        created_at=now,
    )
    idea = SimpleNamespace(
        id=uuid4(),
        generation_id=run.id,
        title="Generated idea",
        problem="Problem",
        feasibility_score=7,
        potential_impact_score=8,
        novelty_score=6,
        details={"title": "Generated idea"},
        created_at=now,
    )
    db = FakeDB(
        chat,
        {
            ArticleSummary: [article],
            DiscoveredProduct: [product],
            LandscapeAnalysisRecord: [analysis],
            IdeaGenerationRun: [run],
            ProjectIdea: [idea],
        },
    )

    result = view_chat_analysis(chat.id, user, db)

    assert result.chat_id == chat.id
    assert [item.title for item in result.articles] == ["Research"]
    assert [item.name for item in result.discovered_products] == [
        "Open source app"
    ]
    assert result.landscape_analyses[0].analysis == {
        "research_summary": "Analysis"
    }
    assert result.idea_generations[0].ideas[0].title == "Generated idea"
    assert db.scalar_calls == 1
    assert len(db.scalars_queries) == 5


def test_view_chat_analysis_rejects_chat_not_owned_by_user():
    db = FakeDB(None, {})
    user = SimpleNamespace(id=uuid4(), user_name="alice")

    with pytest.raises(HTTPException) as error:
        view_chat_analysis(uuid4(), user, db)

    assert error.value.status_code == 404
    assert db.scalar_calls == 1
    assert db.scalars_queries == []
