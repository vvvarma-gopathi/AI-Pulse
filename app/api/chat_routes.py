from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.articles_model import ArticleSummary, Chat, DiscoveredProduct
from app.models.analysis import LandscapeAnalysisRecord
from app.models.auth_model import Users
from app.models.ideas import IdeaGenerationRun, ProjectIdea
from app.schemas.chat import ChatAnalysisResponse, ChatHistoryItem
from app.services.auth_services import get_current_user

chats_router = APIRouter(prefix="/chats", tags=["Chats"])


@chats_router.get("", response_model=list[ChatHistoryItem])
def get_chat_history(
    user: Annotated[Users, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Chat]:
    return db.scalars(
        select(Chat)
        .where(Chat.user_name == user.user_name)
        .order_by(Chat.created_at.desc(), Chat.id.desc())
    ).all()


@chats_router.get(
    "/{chat_id}/analysis",
    response_model=ChatAnalysisResponse,
)
def view_chat_analysis(
    chat_id: UUID,
    user: Annotated[Users, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatAnalysisResponse:
    chat = db.scalar(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_name == user.user_name,
        )
    )
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    articles = db.scalars(
        select(ArticleSummary)
        .where(ArticleSummary.chat_id == chat.id)
        .order_by(ArticleSummary.created_at.desc(), ArticleSummary.id.desc())
    ).all()
    products = db.scalars(
        select(DiscoveredProduct)
        .where(DiscoveredProduct.chat_id == chat.id)
        .order_by(
            DiscoveredProduct.discovered_at.desc(),
            DiscoveredProduct.id.desc(),
        )
    ).all()
    analyses = db.scalars(
        select(LandscapeAnalysisRecord)
        .where(LandscapeAnalysisRecord.chat_id == chat.id)
        .order_by(
            LandscapeAnalysisRecord.created_at.desc(),
            LandscapeAnalysisRecord.id.desc(),
        )
    ).all()
    runs = db.scalars(
        select(IdeaGenerationRun)
        .where(
            IdeaGenerationRun.chat_id == chat.id,
            IdeaGenerationRun.user_id == user.id,
        )
        .order_by(
            IdeaGenerationRun.created_at.desc(),
            IdeaGenerationRun.id.desc(),
        )
    ).all()

    run_ids = [run.id for run in runs]
    ideas = (
        db.scalars(
            select(ProjectIdea)
            .where(ProjectIdea.generation_id.in_(run_ids))
            .order_by(ProjectIdea.created_at, ProjectIdea.id)
        ).all()
        if run_ids
        else []
    )
    ideas_by_run: dict[UUID, list[dict]] = {}
    for idea in ideas:
        ideas_by_run.setdefault(idea.generation_id, []).append(
            {
                "id": idea.id,
                "title": idea.title,
                "problem": idea.problem,
                "feasibility_score": idea.feasibility_score,
                "potential_impact_score": idea.potential_impact_score,
                "novelty_score": idea.novelty_score,
                "details": idea.details,
                "created_at": idea.created_at,
            }
        )

    return ChatAnalysisResponse(
        chat_id=chat.id,
        articles=articles,
        discovered_products=products,
        landscape_analyses=analyses,
        idea_generations=[
            {
                "id": run.id,
                "landscape_analysis_id": run.landscape_analysis_id,
                "generation_mode": run.generation_mode,
                "status": run.status,
                "retrieval_status": run.retrieval_status,
                "overall_summary": run.overall_summary,
                "created_at": run.created_at,
                "ideas": ideas_by_run.get(run.id, []),
            }
            for run in runs
        ],
    )
