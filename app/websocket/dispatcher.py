from collections.abc import Awaitable, Callable

from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.models.auth_model import Users


# Context shared with each handler.
Handler = Callable[
    [dict, WebSocket, Users, Session],
    Awaitable[dict],
]


class WebSocketDispatcher:
    def __init__(self):
        self.handlers = {}

    def register(self, action: str):
        def decorator(handler):
            self.handlers[action] = handler

            print(
                f"REGISTERED: {action}",
                "Dispatcher ID:", id(self),
            )

            return handler

        return decorator

    async def dispatch(
        self, message, websocket, user, db
    ):
        action = message.get("action") or message.get("type")

        print("RECEIVED ACTION:", repr(action))
        print("REGISTERED ACTIONS:", list(self.handlers.keys()))
        print("Dispatcher ID:", id(self))

        handler = self.handlers.get(action)

        if handler is None:
            return {
                "type": "error",
                "message": f"Unknown action: {action}",
            }

        payload = message.get("data", message)
        if not isinstance(payload, dict):
            return {
                "type": "error",
                "message": "Expected a JSON object for the action data",
            }

        return await handler(
            payload,
            websocket,
            user,
            db,
        )


dispatcher = WebSocketDispatcher()