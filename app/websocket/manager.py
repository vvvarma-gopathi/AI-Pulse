from collections import defaultdict
from fastapi import WebSocket
import asyncio


class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = (
            defaultdict(set)
        )
        self.lock = asyncio.Lock()

    async def connect(self, user_name: str, websocket: WebSocket):
        await websocket.accept()

        async with self.lock:
            self.active_connections[user_name].add(websocket)

    async def disconnect(self, user_name: str, websocket: WebSocket):
        async with self.lock:
            connections = self.active_connections.get(user_name)

            if connections:
                connections.discard(websocket)

                if not connections:
                    self.active_connections.pop(user_name, None)

    async def send_to_user(self, user_name: str, message: dict):
        async with self.lock:
            connections = list(
                self.active_connections.get(user_name, set())
            )

        # Don't hold the global lock while performing network I/O.
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                await self.disconnect(user_name, websocket)

    async def broadcast(self, message: dict):
        async with self.lock:
            targets = [
                (user_name, websocket)
                for user_name, connections in self.active_connections.items()
                for websocket in list(connections)
            ]

        for user_name, websocket in targets:
            try:
                await websocket.send_json(message)
            except Exception:
                await self.disconnect(user_name, websocket)


manager = WebSocketManager()