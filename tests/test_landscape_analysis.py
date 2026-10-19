import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.generate_ideas import analysis as landscape_analysis


def test_landscape_result_includes_research_context_and_analysis(monkeypatch):
    chat_id = uuid4()
    research_context = {
        "chat_id": str(chat_id),
        "article_count": 1,
        "technology_count": 1,
        "technologies": ["Python"],
        "articles": [
            {
                "article_id": str(uuid4()),
                "title": "Research article",
                "source_url": "https://example.test/research",
                "summary": "Article summary",
                "technologies": ["Python"],
                "discovered_products": [
                    {
                        "name": "Open-source project",
                        "url": "https://example.test/project",
                        "description": "A discovered project",
                        "evidence_status": "unverified",
                        "search_query": "Python startup",
                    }
                ],
            }
        ],
    }
    analysis = SimpleNamespace(
        model_dump=lambda mode: {"research_summary": "Analysis text"}
    )
    events = []

    class FakeDB:
        def add(self, record):
            self.record = record

        def commit(self):
            pass

        def refresh(self, record):
            record.created_at = datetime.now(timezone.utc)

    async def send_to_user(**kwargs):
        events.append(kwargs["message"])

    monkeypatch.setattr(
        landscape_analysis,
        "build_research_context",
        lambda **_kwargs: research_context,
    )
    monkeypatch.setattr(
        landscape_analysis,
        "analyze_landscape_with_llm",
        lambda _context: analysis,
    )
    monkeypatch.setattr(
        landscape_analysis.manager,
        "send_to_user",
        send_to_user,
    )

    result = asyncio.run(
        landscape_analysis.generate_landscape_analysis(
            db=FakeDB(),
            chat_id=chat_id,
            user_name="researcher",
        )
    )

    assert result["research_context"] == research_context
    assert result["analysis"] == {"research_summary": "Analysis text"}
    assert events[0]["type"] == "analysis"
    assert events[1]["type"] == "analysis"
