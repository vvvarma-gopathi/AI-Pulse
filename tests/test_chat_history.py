from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.api.chat_routes import get_chat_history
from app.schemas.chat import ChatHistoryItem


def test_chat_history_returns_only_authenticated_users_chats():
    user = SimpleNamespace(user_name="authenticated-user")
    chats = [
        SimpleNamespace(
            id=uuid4(),
            user_name=user.user_name,
            title="AI research",
            created_at=datetime.now(timezone.utc),
        )
    ]

    class FakeScalars:
        def all(self):
            return chats

    class FakeDB:
        statement = None

        def scalars(self, statement):
            self.statement = statement
            return FakeScalars()

    db = FakeDB()
    result = get_chat_history(user, db)

    assert result == chats
    assert len(db.statement._where_criteria) == 1
    criterion = db.statement._where_criteria[0]
    assert criterion.left.name == "user_name"
    assert criterion.right.value == user.user_name

    response = ChatHistoryItem.model_validate(result[0])
    assert response.id == chats[0].id
    assert response.title == "AI research"
    assert not hasattr(response, "user_name")
