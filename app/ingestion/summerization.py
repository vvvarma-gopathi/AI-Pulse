
from app.ingestion.summery_prompt import SYSTEM_PROMPT,build_article_prompt
from app.LLM.llm import client
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.schemas.blog_schemas import ArticleSummary as ArticleSummarySchema
from app.schemas.blog_schemas import ArticleSummaryResponse
from google.genai import types
from app.models.articles_model import ArticleSummary,Chat
from app.websocket.manager import manager
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from app.ingestion.dependencies import create_chat_record
from uuid import UUID, uuid4
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def save_article_summaries(
    chat_id: UUID,
    articles: list[ArticleSummarySchema],
    db: Session,
) -> int:
    try:
        chat = db.execute(
            select(Chat).where(Chat.id == chat_id)
        ).scalar_one_or_none()

        if chat is None:
            raise ValueError(f"Chat does not exist: {chat_id}")

        unique_articles = {}
        for item in articles:
            unique_articles.setdefault(item.url, item)

        if not unique_articles:
            return 0

        rows = [
            {
                "id": uuid4(),
                "chat_id": chat.id,
                "title": item.title,
                "summary": item.summary,
                "url": item.url,
                "published_at": item.published_at,
                "technologies": item.technologies,
                "created_at": datetime.now(timezone.utc),
            }
            for item in unique_articles.values()
        ]
        result = db.execute(
            pg_insert(ArticleSummary)
            .values(rows)
            .on_conflict_do_nothing(
                constraint="uq_article_summaries_chat_url"
            )
        )
        db.commit()
        return result.rowcount or 0
    except IntegrityError:
        db.rollback()

        logger.exception(
            "Database integrity error while saving article summaries"
        )
        raise

    except SQLAlchemyError:
        db.rollback()

        logger.exception(
            "Database error while saving article summaries"
        )
        raise





#for clean json response from the model
def clean_json_response(content: str) -> str:
    content = content.strip()

    if content.startswith("```json"):
        content = content[7:]

    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


async def summarize_articles(
    articles: list[dict],
    user_name: str,
    db: Session,
    model: str = "gemini-3.5-flash-lite"
    ) -> list[ArticleSummarySchema]:

    user_prompt = build_article_prompt(articles)

    response = client.models.generate_content(
    model=model,
    contents=user_prompt,
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=ArticleSummaryResponse,
    ),
    )
    raw_content = response.text
    cleaned_content = clean_json_response(raw_content)
    result = ArticleSummaryResponse.model_validate_json(
        cleaned_content
    )
    if not result.articles:
        return []

    chat_record=create_chat_record(
        user_name=user_name,
        title=result.articles[0].title,
        db=db,
    )
    save_article_summaries(
        chat_id=chat_record.id,
        articles=result.articles,
        db=db,
    )
    await manager.send_to_user(
        user_name=user_name,
        message={"data":"successfully saved the retrived information in the database.."},
    )
    return {'summaries':result.articles,'chat_id':chat_record.id}
