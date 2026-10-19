import asyncio
from types import SimpleNamespace

from app.ingestion import fetch
from app.ingestion.queries import QUERY
from app.websocket import handler


class FakeWebSocket:
    def __init__(self):
        self.events = []

    async def send_json(self, event):
        self.events.append(event)


def test_research_search_appends_conditions_to_default_query(monkeypatch):
    searched_queries = []

    async def send_to_user(**_kwargs):
        pass

    monkeypatch.setattr(
        fetch.manager,
        "send_to_user",
        send_to_user,
    )
    monkeypatch.setattr(
        fetch,
        "search_articles",
        lambda query: (searched_queries.append(query) or [], {"credits": 0}),
    )

    result = asyncio.run(
        fetch.SearchTechArticals(
            "researcher",
            object(),
            research_conditions="Focus on open-source AI coding agents",
        )
    )

    assert result == []
    assert searched_queries == [
        f"{QUERY}\n\nAdditional research conditions:\n"
        "Focus on open-source AI coding agents"
    ]


def test_research_search_without_conditions_uses_existing_query(monkeypatch):
    searched_queries = []

    async def send_to_user(**_kwargs):
        pass

    monkeypatch.setattr(fetch.manager, "send_to_user", send_to_user)
    monkeypatch.setattr(
        fetch,
        "search_articles",
        lambda query: (searched_queries.append(query) or [], {"credits": 0}),
    )

    asyncio.run(fetch.SearchTechArticals("researcher", object()))

    assert searched_queries == [QUERY]


def test_research_handler_passes_user_conditions(monkeypatch):
    captured = {}

    async def search(user_name, db, research_conditions=None):
        captured["call"] = user_name, db, research_conditions
        return "chat-id"

    monkeypatch.setattr(handler, "SearchTechArticals", search)
    user = SimpleNamespace(user_name="authenticated")
    db = object()
    websocket = FakeWebSocket()

    result = asyncio.run(
        handler.research_for_articles(
            {"research_conditions": "Focus on AI safety tooling"},
            websocket,
            user,
            db,
        )
    )

    assert result == {
        "type": "search_tech_articles_result",
        "data": "chat-id",
    }
    assert websocket.events == [
        {
            "type": "workflow_step_completed",
            "step": "research_articles",
            "data": "chat-id",
        }
    ]
    assert captured["call"] == (
        "authenticated",
        db,
        "Focus on AI safety tooling",
    )


def test_research_handler_rejects_non_string_conditions(monkeypatch):
    async def unexpected_search(*_args, **_kwargs):
        raise AssertionError("Search should not run for invalid conditions")

    monkeypatch.setattr(handler, "SearchTechArticals", unexpected_search)

    result = asyncio.run(
        handler.research_for_articles(
            {"research_conditions": ["not", "a", "string"]},
            object(),
            SimpleNamespace(user_name="authenticated"),
            object(),
        )
    )

    assert result == {
        "type": "search_tech_articles_failed",
        "error": "research_conditions must be a string",
    }


def test_connection_sends_authenticated_user_details(monkeypatch):
    from api import research_routes
    from fastapi import WebSocketDisconnect

    user = SimpleNamespace(
        id="user-id",
        user_name="authenticated",
        email="user@example.com",
    )

    class ConnectionWebSocket(FakeWebSocket):
        query_params = {"token": "valid-token"}

        async def accept(self):
            pass

        async def receive_json(self):
            raise WebSocketDisconnect()

    websocket = ConnectionWebSocket()
    monkeypatch.setattr(
        research_routes,
        "get_current_user",
        lambda token, _db: user if token == "valid-token" else None,
    )

    asyncio.run(research_routes.authenticate_user(websocket, object()))

    assert websocket.events[0] == {
        "type": "connection_established",
        "data": {
            "user_id": "user-id",
            "username": "authenticated",
            "email": "user@example.com",
        },
    }
