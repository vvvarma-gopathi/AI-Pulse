from fastapi import WebSocket
from sqlalchemy.orm import Session
from start_productions.discovery import discover_recent_articles
from models.articles_model import ArticleSummary
from ingestion.fetch import SearchTechArticals
from generate_ideas.analysis import generate_landscape_analysis

async def research_for_articles(
    data: dict,
    websocket: WebSocket,
    user_name: str,
    db: Session,
) -> dict:
    result = await SearchTechArticals(user_name, db)

    return {
        "type": "search_tech_articles_result",
        "data": result,
    }

async def discover_products(
    data: dict,
    websocket: WebSocket,
    user_name: str,
    db: Session,
) -> dict:
    result=await discover_recent_articles(chat_id=data.get("chat_id"),user_name=user_name)
    return {
            "type": "discover_products_result",
            "data": result
        }

async def analyze_landscape(
    data: dict,
    websocket: WebSocket,
    user_name: str,
    db: Session,
) -> dict:
    result=await generate_landscape_analysis(chat_id=data.get("chat_id"),user_name=user_name,db=db)
    return {
            "type": "analyze_landscape_result",
            "data": result
        }
