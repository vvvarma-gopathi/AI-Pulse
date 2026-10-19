import logging

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.generate_ideas.analysis import generate_landscape_analysis
from app.generate_ideas.ideas_service import generate_project_ideas
from app.models.auth_model import Users
from app.schemas.ideas import IdeaGenerationRequest
from app.ingestion.fetch import SearchTechArticals
from app.start_productions.discovery import discover_recent_articles

logger = logging.getLogger(__name__)


async def _send_step_completed(
    websocket: WebSocket,
    step: str,
    result,
) -> None:
    await websocket.send_json(
        {
            "type": "workflow_step_completed",
            "step": step,
            "data": jsonable_encoder(result),
        }
    )


async def research_for_articles(
    data: dict,
    websocket: WebSocket,
    user: Users,
    db: Session,
) -> dict:
    research_conditions = data.get("research_conditions")
    if research_conditions is not None and not isinstance(
        research_conditions,
        str,
    ):
        return {
            "type": "search_tech_articles_failed",
            "error": "research_conditions must be a string",
        }

    result = await SearchTechArticals(
        user.user_name,
        db,
        research_conditions=research_conditions,
    )
    await _send_step_completed(websocket, "research_articles", result)

    return {
        "type": "search_tech_articles_result",
        "data": result,
    }

async def discover_products(
    data: dict,
    websocket: WebSocket,
    user: Users,
    db: Session,
) -> dict:
    result=await discover_recent_articles(
        chat_id=data.get("chat_id"),
        user_name=user.user_name,
    )
    await _send_step_completed(websocket, "discover_products", result)
    return {
            "type": "discover_products_result",
            "data": result
        }

async def analyze_landscape(
    data: dict,
    websocket: WebSocket,
    user: Users,
    db: Session,
) -> dict:
    result=await generate_landscape_analysis(
        chat_id=data.get("chat_id"),
        user_name=user.user_name,
        db=db,
    )
    await _send_step_completed(websocket, "analyze_landscape", result)
    return {
        "type": "analyze_landscape_result",
        "data": "landscape analysis completed successfully"
    }


async def generate_ideas(
    data: dict,
    websocket: WebSocket,
    user: Users,
    db: Session,
) -> dict:
    request_id = str(data.get("request_id") or "")[:64]
    generation_id = ""
    try:
        request = IdeaGenerationRequest.model_validate(data)

        async def send_progress(event: dict) -> None:
            nonlocal generation_id
            generation_id = event.get("generation_id", generation_id)
            await websocket.send_json(event)

        result = await generate_project_ideas(
            db=db,
            user=user,
            request=request,
            progress=send_progress,
        )
        return {
            "type": "idea_generation_result",
            "request_id": str(request.request_id),
            "data": result,
            "status": "completed",
        }
    except ValidationError:
        logger.exception("Invalid idea generation request")
        error = "Invalid idea generation request"
    except PermissionError:
        logger.exception("Idea generation access denied for user %s", user.id)
        error = "The requested analysis or project is not available"
    except ValueError as exc:
        logger.exception("Idea generation request could not be completed")
        error = "The request could not be completed with the supplied data"
    except Exception:
        logger.exception(
            "Unexpected idea generation failure for user %s",
            user.id,
        )
        error = "Idea generation failed. Please retry later."

    await websocket.send_json(
        {
            "type": "idea_generation_failed",
            "request_id": request_id,
            "generation_id": generation_id or None,
            "error": error,
        }
    )
    return {
        "type": "idea_generation_failure_ack",
        "request_id": request_id,
    }
