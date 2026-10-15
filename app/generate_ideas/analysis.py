import json
import os
import logging
from uuid import UUID
from websocket.manager import manager
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.orm import Session
from core.config import settings

from models.articles_model import ArticleSummary
from models.articles_model import DiscoveredProduct
from models.analysis import LandscapeAnalysisRecord
from LLM.llm import client
from schemas.analysis_schemas import LandscapeAnalysis
from generate_ideas.prompts.analysis_prompt import LANDSCAPE_SYSTEM_PROMPT


load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
)

PROMPT_VERSION = "landscape-v1"

MAX_ARTICLES = 50
MAX_PRODUCTS_PER_ARTICLE = 10
MAX_SUMMARY_LENGTH = 2000

def normalize_technologies(value) -> list[str]:
    """
    Normalize technology data stored as JSON.

    Supports:
    ["Python", "FastAPI"]

    Also supports:
    [{"name": "Python"}, {"name": "FastAPI"}]
    """
    if not value:
        return []

    if not isinstance(value, list):
        return []

    technologies = []
    seen = set()

    for item in value:
        if isinstance(item, str):
            name = item.strip()

        elif isinstance(item, dict):
            name = str(item.get("name", "")).strip()

        else:
            continue

        if not name:
            continue

        # Preserve the original spelling while deduplicating.
        key = name.casefold()

        if key not in seen:
            seen.add(key)
            technologies.append(name)

    return technologies


def build_research_context(
    db: Session,
    chat_id: UUID,
    max_articles: int = 30,
    include_unverified_products: bool = True,
) -> dict:
    """
    Load article summaries and their discovered products.

    Returns a JSON-serializable research context.
    """

    max_articles = max(1, min(max_articles, MAX_ARTICLES))

    article_statement = (
        select(ArticleSummary)
        .where(ArticleSummary.chat_id == chat_id)
        .order_by(ArticleSummary.created_at.desc())
        .limit(max_articles)
    )

    articles = db.scalars(article_statement).all()

    if not articles:
        raise ValueError(
            "No article summaries found for this research batch"
        )

    article_ids = [article.id for article in articles]

    product_statement = (
        select(DiscoveredProduct)
        .where(
            DiscoveredProduct.article_summary_id.in_(article_ids)
        )
        .order_by(DiscoveredProduct.discovered_at.desc())
    )

    if not include_unverified_products:
        product_statement = product_statement.where(
            DiscoveredProduct.evidence_status != "unverified"
        )

    products = db.scalars(product_statement).all()

    # Associate products with the article that led to their discovery.
    products_by_article = {}

    for product in products:
        article_id = str(product.article_summary_id)

        products_by_article.setdefault(
            article_id,
            [],
        )

        if (
            len(products_by_article[article_id])
            >= MAX_PRODUCTS_PER_ARTICLE
        ):
            continue

        products_by_article[article_id].append(
            {
                "name": product.name,
                "url": product.candidate_url,
                "description": (
                    (product.description or "")[:1000]
                ),
                "evidence_status": (
                    product.evidence_status or "unknown"
                ),
                "search_query": product.search_query,
            }
        )

    research_articles = []
    all_technologies = {}

    for article in articles:
        article_id = str(article.id)

        technologies = normalize_technologies(
            article.technologies
        )

        for technology in technologies:
            all_technologies.setdefault(
                technology.casefold(),
                technology,
            )

        research_articles.append(
            {
                "article_id": article_id,
                "title": article.title,
                "source_url": article.url,
                "summary": (
                    (article.summary or "")[:MAX_SUMMARY_LENGTH]
                ),
                "technologies": technologies,
                "discovered_products": products_by_article.get(
                    article_id,
                    [],
                ),
            }
        )

    return {
        "chat_id": str(chat_id),
        "article_count": len(research_articles),
        "technology_count": len(all_technologies),
        "technologies": list(all_technologies.values()),
        "articles": research_articles,
    }


def analyze_landscape_with_llm(
    research_context: dict,
) -> LandscapeAnalysis:
    """
    Send research context to Gemini and validate its response.
    """

    prompt_data = json.dumps(
        research_context,
        ensure_ascii=False,
    )

    response = client.models.generate_content(
        model=settings.GeminiModel,
        contents=(
            "Analyze the following research context according "
            "to your system instructions.\n\n"
            "RESEARCH_CONTEXT_JSON:\n"
            f"{prompt_data}"
        ),
        config=types.GenerateContentConfig(
            system_instruction=LANDSCAPE_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=LandscapeAnalysis,
            temperature=0.2,
        ),
    )

    # Prefer the SDK's parsed structured response.
    if response.parsed is not None:
        if isinstance(response.parsed, LandscapeAnalysis):
            return response.parsed

        return LandscapeAnalysis.model_validate(
            response.parsed
        )

    # Fallback if the SDK provides JSON text but no parsed object.
    if not response.text:
        raise RuntimeError(
            "The LLM returned an empty landscape analysis"
        )

    return LandscapeAnalysis.model_validate_json(
        response.text
    )


async def generate_landscape_analysis(
    db: Session,
    chat_id: UUID,
    user_name:str,
    max_articles: int = 30,
    include_unverified_products: bool = True,
) -> dict:
    """
    Complete Stage 1 workflow.

    Builds context -> calls LLM -> validates -> persists.
    """
    await manager.send_to_user(user_name=user_name,message={'type':"analysis","data":"building research context for you....."})
    research_context = build_research_context(
        db=db,
        chat_id=chat_id,
        max_articles=max_articles,
        include_unverified_products=include_unverified_products,
    )
    await manager.send_to_user(user_name=user_name,message={'type':"analysis","data":"analyzing the research context...."})
    analysis = analyze_landscape_with_llm(
        research_context
    )

    # Persist only after successful validation.
    record = LandscapeAnalysisRecord(
        chat_id=chat_id,
        input_summary_ids=[
            article["article_id"]
            for article in research_context["articles"]
        ],
        model_name=MODEL_NAME,
        prompt_version=PROMPT_VERSION,
        analysis=analysis.model_dump(mode="json"),
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to persist landscape analysis"
        )
        raise

    return {
        "analysis_id": str(record.id),
        "chat_id": str(record.chat_id),
        "model_name": record.model_name,
        "prompt_version": record.prompt_version,
        "article_count": research_context["article_count"],
        "technology_count": research_context["technology_count"],
        "analysis": analysis.model_dump(mode="json"),
        "created_at": record.created_at.isoformat(),
    }