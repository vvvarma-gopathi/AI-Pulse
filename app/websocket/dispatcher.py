from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import WebSocket
from sqlalchemy.orm import Session


# Context shared with each handler.
Handler = Callable[
    [dict, WebSocket, str, Session],
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
        self, message, websocket, user_name, db
    ):
        action = message.get("action")

        print("RECEIVED ACTION:", repr(action))
        print("REGISTERED ACTIONS:", list(self.handlers.keys()))
        print("Dispatcher ID:", id(self))

        handler = self.handlers.get(action)

        if handler is None:
            return {
                "type": "error",
                "message": f"Unknown action: {action}",
            }

        return await handler(
            message.get("data", {}),
            websocket,
            user_name,
            db,
        )


dispatcher = WebSocketDispatcher()