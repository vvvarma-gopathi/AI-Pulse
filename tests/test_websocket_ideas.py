import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.websocket import handler as websocket_handler
from app.schemas.ideas import IdeaGenerationRequest
from app.websocket.dispatcher import WebSocketDispatcher


def test_client_user_id_does_not_override_authenticated_identity():
    auth_user = SimpleNamespace(id=uuid4(), user_name="authenticated")
    seen = {}
    dispatcher = WebSocketDispatcher()

    async def handler(data, _websocket, user, _db):
        seen["user"] = user
        seen["client_user_id"] = data.get("user_id")
        return {}

    dispatcher.register("generate_ideas")(handler)
    request = {
        "type": "generate_ideas",
        "landscape_analysis_id": str(uuid4()),
        "user_id": str(uuid4()),
    }

    asyncio.run(
        dispatcher.dispatch(
            request,
            websocket=object(),
            user=auth_user,
            db=object(),
        )
    )

    parsed = IdeaGenerationRequest.model_validate(request)
    assert seen["user"] is auth_user
    assert seen["client_user_id"] == request["user_id"]
    assert not hasattr(parsed, "user_id")


def test_dispatch_supports_legacy_action_data_shape_and_flat_type_shape():
    authenticated_user = SimpleNamespace(id=uuid4())
    received = []
    dispatcher = WebSocketDispatcher()

    async def handler(data, _websocket, user, _db):
        received.append((data, user))
        return {}

    dispatcher.register("generate_ideas")(handler)
    asyncio.run(
        dispatcher.dispatch(
            {
                "action": "generate_ideas",
                "data": {"landscape_analysis_id": str(uuid4())},
            },
            object(),
            authenticated_user,
            object(),
        )
    )
    asyncio.run(
        dispatcher.dispatch(
            {
                "type": "generate_ideas",
                "landscape_analysis_id": str(uuid4()),
            },
            object(),
            authenticated_user,
            object(),
        )
    )

    assert received[0][0].keys() == {"landscape_analysis_id"}
    assert received[1][0]["type"] == "generate_ideas"
    assert received[0][1] is authenticated_user
    assert received[1][1] is authenticated_user


def test_concurrent_requests_keep_authenticated_user_context_isolated():
    first_user = SimpleNamespace(id=uuid4())
    second_user = SimpleNamespace(id=uuid4())
    dispatcher = WebSocketDispatcher()
    results = {}

    async def handler(data, _websocket, user, _db):
        await asyncio.sleep(0)
        results[data["request_id"]] = user.id
        return {}

    dispatcher.register("generate_ideas")(handler)

    async def run_requests():
        await asyncio.gather(
            dispatcher.dispatch(
                {"type": "generate_ideas", "request_id": "first"},
                object(),
                first_user,
                object(),
            ),
            dispatcher.dispatch(
                {"type": "generate_ideas", "request_id": "second"},
                object(),
                second_user,
                object(),
            ),
        )

    asyncio.run(run_requests())

    assert results == {
        "first": first_user.id,
        "second": second_user.id,
    }


def test_failure_event_includes_request_and_generation_ids_without_exception(
    monkeypatch,
):
    request_id = str(uuid4())
    generation_id = str(uuid4())
    events = []

    class FakeWebSocket:
        async def send_json(self, event):
            events.append(event)

    async def fail_after_start(*_args, progress, **_kwargs):
        await progress(
            {
                "type": "idea_generation_started",
                "request_id": request_id,
                "generation_id": generation_id,
            }
        )
        raise RuntimeError("private provider credential")

    monkeypatch.setattr(
        websocket_handler,
        "generate_project_ideas",
        fail_after_start,
    )

    result = asyncio.run(
        websocket_handler.generate_ideas(
            {
                "request_id": request_id,
                "landscape_analysis_id": str(uuid4()),
            },
            FakeWebSocket(),
            SimpleNamespace(id=uuid4()),
            object(),
        )
    )

    failure_event = events[-1]
    assert failure_event["type"] == "idea_generation_failed"
    assert failure_event["request_id"] == request_id
    assert failure_event["generation_id"] == generation_id
    assert "private provider credential" not in failure_event["error"]
    assert result["type"] == "idea_generation_failure_ack"


def test_successful_workflow_actions_emit_step_completion_events(monkeypatch):
    events = []
    user = SimpleNamespace(id=uuid4(), user_name="authenticated")
    db = object()
    expected_user = user
    expected_db = db
    analysis_id = uuid4()

    class FakeWebSocket:
        async def send_json(self, event):
            events.append(event)

    async def discover(*, chat_id, user_name):
        assert chat_id == "chat-id"
        assert user_name == user.user_name
        return [{"products_discovered": 2}]

    async def analyze(*, chat_id, user_name, db):
        assert chat_id == "chat-id"
        assert user_name == user.user_name
        assert db is expected_db
        return {
            "analysis_id": str(analysis_id),
            "research_context": {
                "articles": [
                    {
                        "title": "Research article",
                        "discovered_products": [
                            {"name": "Open-source project"}
                        ],
                    }
                ]
            },
            "analysis": {"research_summary": "Analysis text"},
        }

    async def generate(*, db, user, request, progress):
        assert db is expected_db
        assert user is expected_user
        assert request.landscape_analysis_id == analysis_id
        return {
            "generation_id": "generation-id",
            "ideas": [
                {
                    "title": "Research-backed workflow assistant",
                    "problem": "Teams lose time resolving a documented bottleneck.",
                    "proposed_solution": (
                        "A focused tool that automates that workflow."
                    ),
                }
            ],
        }

    monkeypatch.setattr(
        websocket_handler,
        "discover_recent_articles",
        discover,
    )
    monkeypatch.setattr(
        websocket_handler,
        "generate_landscape_analysis",
        analyze,
    )
    monkeypatch.setattr(
        websocket_handler,
        "generate_project_ideas",
        generate,
    )

    async def run_actions():
        websocket = FakeWebSocket()
        await websocket_handler.discover_products(
            {"chat_id": "chat-id"},
            websocket,
            user,
            db,
        )
        await websocket_handler.analyze_landscape(
            {"chat_id": "chat-id"},
            websocket,
            user,
            db,
        )
        await websocket_handler.generate_ideas(
            {"landscape_analysis_id": str(analysis_id)},
            websocket,
            user,
            db,
        )

    asyncio.run(run_actions())

    assert [event["step"] for event in events] == [
        "discover_products",
        "analyze_landscape",
    ]
    assert all(
        event["type"] == "workflow_step_completed"
        for event in events
    )
    analysis_event = next(
        event
        for event in events
        if event["step"] == "analyze_landscape"
    )
    assert analysis_event["data"]["research_context"]["articles"][0][
        "discovered_products"
    ][0]["name"] == "Open-source project"
    assert analysis_event["data"]["analysis"] == {
        "research_summary": "Analysis text"
    }


def test_idea_generation_returns_idea_details_without_analysis_event(
    monkeypatch,
):
    events = []
    idea_details = {
        "title": "Research-backed workflow assistant",
        "problem": "Teams lose time resolving a documented bottleneck.",
        "proposed_solution": "A focused tool that automates that workflow.",
    }

    class FakeWebSocket:
        async def send_json(self, event):
            events.append(event)

    async def generate(*, progress, **_kwargs):
        await progress(
            {
                "type": "idea_generation_started",
                "request_id": "request-id",
                "generation_id": "generation-id",
            }
        )
        return {
            "generation_id": "generation-id",
            "ideas": [idea_details],
        }

    monkeypatch.setattr(
        websocket_handler,
        "generate_project_ideas",
        generate,
    )
    request_id = str(uuid4())
    result = asyncio.run(
        websocket_handler.generate_ideas(
            {
                "request_id": request_id,
                "landscape_analysis_id": str(uuid4()),
            },
            FakeWebSocket(),
            SimpleNamespace(id=uuid4()),
            object(),
        )
    )

    assert [event["type"] for event in events] == [
        "idea_generation_started"
    ]
    assert result["type"] == "idea_generation_result"
    assert result["data"]["ideas"] == [idea_details]
    assert result["data"]["ideas"][0]["problem"]
    assert result["data"]["ideas"][0]["proposed_solution"]
