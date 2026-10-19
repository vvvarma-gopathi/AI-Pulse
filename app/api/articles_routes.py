from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.articles_model import ArticleSummary
from app.schemas.blog_schemas import HomepageArticleResponse

articles_router = APIRouter(prefix="/articles", tags=["Articles"])


@articles_router.get("", response_model=list[HomepageArticleResponse])
def list_homepage_articles(
    db: Annotated[Session, Depends(get_db)],
) -> list[ArticleSummary]:
    return db.scalars(
        select(ArticleSummary)
        .order_by(
            ArticleSummary.created_at.desc(),
            ArticleSummary.id.desc(),
        )
        .limit(10)
    ).all()
