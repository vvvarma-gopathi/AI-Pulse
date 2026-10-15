import json
import logging
from uuid import UUID
from core.config import settings
from google.genai import types
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.articles_model import ArticleSummary
from models.analysis import LandscapeAnalysisRecord
from models.ideas import (
    IdeaGenerationRun,
    ProjectIdea,
)
from schemas.ideas import (
    IdeaGenerationRequest,
    IdeaGenerationResponse,
)

from prompts.idea_generation_prompt import (
    IDEA_GENERATION_SYSTEM_PROMPT,
)
from LLM.llm import client


logger = logging.getLogger(__name__)

def load_stage1_context(
    db: Session,
    landscape_analysis_id: UUID,
) -> tuple[LandscapeAnalysisRecord, dict]:
    """
    Load a previously persisted Stage 1 analysis and its sources.
    Does not call the LLM or repeat landscape analysis.

    """

    record = db.get(
        LandscapeAnalysisRecord,
        landscape_analysis_id,
    )

    if record is None:
        raise ValueError(
            "Landscape analysis not found"
        )

    summary_ids = record.input_summary_ids or []

    if not summary_ids:
        raise ValueError(
            "Landscape analysis contains no source article IDs"
        )

    # Load the original summaries to verify source IDs and URLs.
    articles = db.scalars(
        select(ArticleSummary).where(
            ArticleSummary.id.in_(summary_ids),
            ArticleSummary.chat_id == record.chat_id,
        )
    ).all()

    articles_by_id = {
        str(article.id): article
        for article in articles
    }

    source_catalog = []

    for summary_id in summary_ids:
        article = articles_by_id.get(str(summary_id))

        if article is None:
            continue

        source_catalog.append(
            {
                "article_id": str(article.id),
                "title": article.title,
                "source_url": article.url,
                "summary": (article.summary or "")[:1500],
                "technologies": article.technologies or [],
            }
        )

    if not source_catalog:
        raise ValueError(
            "No original article summaries remain available "
            "for this landscape analysis"
        )

    context = {
        "landscape_analysis_id": str(record.id),
        "chat_id": str(record.chat_id),
        "landscape_analysis": record.analysis,
        "source_catalog": source_catalog,
    }

    return record, context


def build_idea_generation_prompt(
    context: dict,
    request: IdeaGenerationRequest,
) -> str:
    """
    Construct the user prompt for the selected generation mode.
    """

    mode_instructions = {
        "new_product": (
            "Generate new software product or startup concepts "
            "from the landscape, reported problems, and potential gaps."
        ),
        "project_improvement": (
            "Identify concrete improvements for the supplied project. "
            "Tie each recommendation to the project's existing "
            "capabilities and the research evidence."
        ),
        "technology_combination": (
            "Generate ideas that use meaningful combinations of "
            "technologies from the research. Explain what the "
            "combination enables and why it is useful."
        ),
    }

    payload = {
        "generation_mode": request.mode,
        "requested_idea_count": request.number_of_ideas,
        "existing_project_description": (
            request.existing_project_description
        ),
        "mode_instructions": mode_instructions[request.mode],
        "research_context": context,
    }

    return (
        "Generate project ideas using the following structured "
        "research context. Follow the system instructions and "
        "return the requested structured response.\n\n"
        "INPUT_JSON:\n"
        + json.dumps(payload, ensure_ascii=False)
    )


def generate_ideas_with_llm(
    context: dict,
    request: IdeaGenerationRequest,
) -> IdeaGenerationResponse:
    """
    Call Gemini and validate the structured output.
    """

    prompt = build_idea_generation_prompt(
        context,
        request,
    )

    response = client.models.generate_content(
        model=settings.GeminiModel,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=IDEA_GENERATION_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=IdeaGenerationResponse,
            temperature=0.5,
        ),
    )

    if response.parsed is not None:
        if isinstance(
            response.parsed,
            IdeaGenerationResponse,
        ):
            result = response.parsed
        else:
            result = IdeaGenerationResponse.model_validate(
                response.parsed
            )

    elif response.text:
        result = IdeaGenerationResponse.model_validate_json(
            response.text
        )

    else:
        raise RuntimeError(
            "The LLM returned an empty idea-generation response"
        )

    # The model must not control which analysis or mode the
    # response claims to belong to. Set these from the request.
    result = result.model_copy(
        update={
            "research_analysis_id": context[
                "landscape_analysis_id"
            ],
            "generation_mode": request.mode,
        }
    )

    return result


def validate_idea_evidence(
    result: IdeaGenerationResponse,
    context: dict,
) -> None:
    """
    Reject source references that do not match the source catalog.
    """

    allowed_sources = {
        item["article_id"]: item["source_url"]
        for item in context["source_catalog"]
    }

    for idea in result.ideas:
        for evidence in idea.evidence:
            expected_url = allowed_sources.get(
                evidence.article_id
            )

            if expected_url is None:
                raise ValueError(
                    "The LLM referenced an unknown article ID: "
                    f"{evidence.article_id}"
                )

            if evidence.source_url != expected_url:
                raise ValueError(
                    "The LLM returned a URL that does not match "
                    f"article {evidence.article_id}"
                )


def persist_ideas(
    db: Session,
    landscape_record: LandscapeAnalysisRecord,
    result: IdeaGenerationResponse,
) -> dict:
    """
    Persist one generation run and its individual ideas atomically.
    """

    run = IdeaGenerationRun(
        landscape_analysis_id=landscape_record.id,
        chat_id=landscape_record.chat_id,
        generation_mode=result.generation_mode,
        model_name=settings.GeminiModel,
        prompt_version='idea_generation_v1',
        overall_summary=result.overall_summary,
    )

    try:
        db.add(run)
        db.flush()

        for idea in result.ideas:
            db.add(
                ProjectIdea(
                    generation_id=run.id,
                    title=idea.title,
                    problem=idea.problem,
                    feasibility_score=idea.feasibility_score,
                    potential_impact_score=(
                        idea.potential_impact_score
                    ),
                    novelty_score=idea.novelty_score,
                    details=idea.model_dump(mode="json"),
                )
            )

        db.commit()
        db.refresh(run)

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to persist idea generation results"
        )
        raise

    return {
        "generation_id": str(run.id),
        "landscape_analysis_id": str(
            landscape_record.id
        ),
        "chat_id": str(run.chat_id),
        "model_name": run.model_name,
        "generation_mode": run.generation_mode,
        "overall_summary": run.overall_summary,
        "ideas": result.ideas,
        "created_at": run.created_at.isoformat(),
    }


def generate_project_ideas(
    db: Session,
    request: IdeaGenerationRequest,
) -> dict:
    """
    Complete Stage 2:
    Load Stage 1 -> build context -> generate -> validate -> save.
    """

    landscape_id = UUID(
        request.landscape_analysis_id
    )

    if (
        request.mode == "project_improvement"
        and not request.existing_project_description
    ):
        raise ValueError(
            "existing_project_description is required "
            "for project_improvement mode"
        )

    landscape_record, context = load_stage1_context(
        db,
        landscape_id,
    )

    result = generate_ideas_with_llm(
        context,
        request,
    )

    validate_idea_evidence(
        result,
        context,
    )

    return persist_ideas(
        db,
        landscape_record,
        result,
    )