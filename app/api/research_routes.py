from fastapi import APIRouter,Depends,WebSocket,WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from typing import Annotated
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.websocket.manager import manager
from app.websocket.dispatcher import dispatcher
from app.websocket.handler import (
    analyze_landscape,
    discover_products,
    generate_ideas,
    research_for_articles,
)
from app.services.auth_services import get_current_user

research_router=APIRouter(prefix="/research/ws",tags=["Research"])
dispatcher.register("search_tech_articles")(research_for_articles)
dispatcher.register("discover_products")(discover_products)
dispatcher.register("analysis")(analyze_landscape)
dispatcher.register("generate_ideas")(generate_ideas)

@research_router.websocket("")
async def authenticate_user(websocket:WebSocket,db:Annotated[Session,Depends(get_db)]):
    token = websocket.query_params.get("token")
    user = get_current_user(token, db) if token else None
    if user is None:
        # Before accept(), this rejects the handshake.
        await websocket.close(code=1008)
        return

    user_name=user.user_name
    
    await manager.connect(user_name, websocket)

    try:
        await websocket.send_json(
            {
                "type": "connection_established",
                "data": {
                    "user_id": str(user.id),
                    "username": user.user_name,
                    "email": user.email,
                },
            }
        )

        while True:
            message = await websocket.receive_json()

            if not isinstance(message, dict):
                await websocket.send_json({
                    "type": "error",
                    "message": "Expected a JSON object",
                })
                continue

            response = await dispatcher.dispatch(
                message=message,
                websocket=websocket,
                user=user,
                db=db,
            )

            await websocket.send_json(jsonable_encoder(response))

    except WebSocketDisconnect:
        pass

    finally:
        await manager.disconnect(user_name, websocket)
