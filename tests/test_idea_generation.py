import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.generate_ideas import ideas_service
from app.schemas.ideas import (
    GeneratedIdea,
    IdeaEvidence,
    IdeaGenerationRequest,
    IdeaGenerationResponse,
)


def make_idea(article_id: str, source_url: str) -> GeneratedIdea:
    return GeneratedIdea(
        title="Research-backed workflow assistant",
        tagline="Automate a real, narrow workflow",
        problem="Teams spend time resolving a documented bottleneck.",
        target_users=["Engineering teams"],
        proposed_solution="A focused tool that addresses that bottleneck.",
        core_features=["Workflow integration"],
        technologies=["Python"],
        differentiation="Designed for a specific documented workflow.",
        similar_products=[],
        supporting_evidence=[
            IdeaEvidence(
                article_id=article_id,
                source_url=source_url,
                explanation="The article describes the related problem.",
            )
        ],
        personalization_rationale="No existing project was relevant.",
        assumptions=["The reported need affects the target users."],
        feasibility_score=7,
        potential_impact_score=6,
        novelty_score=5,
        score_rationale="Preliminary estimates based on limited research.",
        mvp_scope=["One workflow integration"],
        validation_steps=["Interview target users"],
    )


def test_fabricated_article_references_are_rejected():
    url = "https://example.test/research"
    result = IdeaGenerationResponse(
        research_analysis_id=str(uuid4()),
        generation_mode="new_product",
        overall_summary="One supported opportunity.",
        ideas=[make_idea(str(uuid4()), url)],
    )

    with pytest.raises(ValueError, match="unsupported article reference"):
        ideas_service.validate_idea_evidence(
            result,
            {
                "source_catalog": [
                    {
                        "article_id": str(uuid4()),
                        "source_url": url,
                    }
                ]
            },
        )


def test_unseen_similar_products_are_rejected():
    article_id = str(uuid4())
    source_url = "https://example.test/research"
    result = IdeaGenerationResponse(
        research_analysis_id=str(uuid4()),
        generation_mode="new_product",
        overall_summary="One supported opportunity.",
        ideas=[
            make_idea(article_id, source_url).model_copy(
                update={"similar_products": ["Invented company"]}
            )
        ],
    )

    with pytest.raises(ValueError, match="unsupported similar product"):
        ideas_service.validate_idea_evidence(
            result,
            {
                "source_catalog": [
                    {
                        "article_id": article_id,
                        "source_url": source_url,
                        "discovered_products": [],
                    }
                ],
                "landscape_analysis": {"product_landscape": []},
            },
        )


def test_unsupported_similar_products_are_removed_before_validation():
    article_id = str(uuid4())
    source_url = "https://example.test/research"
    result = IdeaGenerationResponse(
        research_analysis_id=str(uuid4()),
        generation_mode="new_product",
        overall_summary="One supported opportunity.",
        ideas=[
            make_idea(article_id, source_url).model_copy(
                update={
                    "similar_products": [
                        "Known product",
                        "Invented company",
                    ]
                }
            )
        ],
    )
    context = {
        "source_catalog": [
            {
                "article_id": article_id,
                "source_url": source_url,
                "discovered_products": [{"name": "Known product"}],
            }
        ],
        "landscape_analysis": {"product_landscape": []},
    }

    sanitized, removed_count = (
        ideas_service.remove_unsupported_similar_products(
            result,
            context,
        )
    )

    assert removed_count == 1
    assert sanitized.ideas[0].similar_products == ["Known product"]
    ideas_service.validate_idea_evidence(sanitized, context)


def test_unsupported_article_reference_retries_with_allowed_citations(
    monkeypatch,
):
    article_id = str(uuid4())
    analysis_id = uuid4()
    source_url = "https://example.test/research"
    context = {
        "landscape_analysis_id": str(analysis_id),
        "landscape_analysis": {},
        "source_catalog": [
            {
                "article_id": article_id,
                "source_url": source_url,
            }
        ],
        "technologies": [],
    }
    request = IdeaGenerationRequest(
        landscape_analysis_id=analysis_id,
        mode="new_product",
        number_of_ideas=1,
    )
    invalid_result = IdeaGenerationResponse(
        research_analysis_id=str(analysis_id),
        generation_mode="new_product",
        overall_summary="An idea based on the research.",
        ideas=[make_idea(str(uuid4()), source_url)],
    )
    valid_result = IdeaGenerationResponse(
        research_analysis_id=str(analysis_id),
        generation_mode="new_product",
        overall_summary="An idea based on the research.",
        ideas=[make_idea(article_id, source_url)],
    )
    calls = []

    def generate(context_arg, _request):
        calls.append(context_arg)
        return invalid_result if len(calls) == 1 else valid_result

    monkeypatch.setattr(
        ideas_service,
        "generate_ideas_with_llm",
        generate,
    )

    result, removed_products = (
        ideas_service.generate_ideas_with_evidence_retry(context, request)
    )

    assert len(calls) == 2
    assert "_citation_retry_guidance" not in calls[0]
    assert "allowed_article_references" in (
        ideas_service.build_idea_generation_prompt(context, request)
    )
    assert "_citation_retry_guidance" not in (
        ideas_service.build_idea_generation_prompt(calls[1], request)
    )
    assert "unsupported article reference" in (
        ideas_service.build_idea_generation_prompt(calls[1], request)
    )
    assert result.ideas[0].supporting_evidence[0].article_id == article_id
    assert removed_products == 0


def test_empty_rag_results_still_generate_research_only_ideas(monkeypatch):
    async def run_test():
        article_id = uuid4()
        analysis_id = uuid4()
        request_id = uuid4()
        source_url = "https://example.test/research"
        context = {
            "landscape_analysis_id": str(analysis_id),
            "landscape_analysis": {
                "research_summary": "A clear research trend."
            },
            "source_catalog": [
                {
                    "article_id": str(article_id),
                    "source_url": source_url,
                }
            ],
            "technologies": ["Python"],
        }
        record = SimpleNamespace(id=analysis_id, chat_id=uuid4())
        user = SimpleNamespace(id=uuid4(), user_name="alice")
        request = IdeaGenerationRequest(
            request_id=request_id,
            landscape_analysis_id=analysis_id,
            mode="new_product",
            number_of_ideas=1,
        )
        events = []

        class FakeDB:
            def __init__(self):
                self.added = []
                self.added_many = []

            def add(self, item):
                if not getattr(item, "id", None):
                    item.id = uuid4()
                if not getattr(item, "created_at", None):
                    item.created_at = datetime.now(timezone.utc)
                self.added.append(item)

            def add_all(self, items):
                self.added_many.extend(items)

            def commit(self):
                pass

            def refresh(self, item):
                pass

            def scalars(self, _statement):
                return SimpleNamespace(all=lambda: self.added_many)

        db = FakeDB()
        monkeypatch.setattr(
            ideas_service,
            "_get_existing_run",
            lambda *_args: None,
        )
        monkeypatch.setattr(
            ideas_service,
            "load_stage1_context",
            lambda *_args: (record, context),
        )

        async def empty_retrieval(*_args, **_kwargs):
            return [], []

        monkeypatch.setattr(
            ideas_service,
            "retrieve_project_context_async",
            empty_retrieval,
        )
        monkeypatch.setattr(
            ideas_service,
            "generate_ideas_with_llm",
            lambda _context, _request: IdeaGenerationResponse(
                research_analysis_id=str(analysis_id),
                generation_mode="new_product",
                overall_summary="Research supports one idea.",
                ideas=[make_idea(str(article_id), source_url)],
            ),
        )

        async def collect(event):
            events.append(event)

        result = await ideas_service.generate_project_ideas(
            db,
            user,
            request,
            collect,
        )

        assert result["retrieval_status"] == "completed"
        assert result["project_ids_used"] == []
        assert len(result["ideas"]) == 1
        assert {event["type"] for event in events} >= {
            "idea_generation_started",
            "retrieval_started",
            "retrieval_completed",
            "idea_generation_completed",
        }
        assert all(
            event["request_id"] == str(request_id) for event in events
        )
        assert result["generation_id"] == str(db.added[0].id)
        assert db.added[0].status == "completed"
        assert len(db.added_many) == 1

    asyncio.run(run_test())
