from fastapi import APIRouter,Depends,WebSocket,WebSocketDisconnect
from typing import Annotated
from core.database import get_db
from sqlalchemy.orm import Session
from websocket.manager import manager
from websocket.dispatcher import dispatcher
from websocket.handler import discover_products, research_for_articles,analyze_landscape
from services.auth_services import get_current_user

research_router=APIRouter(prefix="/research/ws",tags=["Research"])
dispatcher.register("search_tech_articles")(research_for_articles)
dispatcher.register("discover_products")(discover_products)
dispatcher.register("analysis")(analyze_landscape)

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
                user_name=user_name,
                db=db,
            )

            await websocket.send_json(response)

    except WebSocketDisconnect:
        pass

    finally:
        await manager.disconnect(user_name, websocket)
