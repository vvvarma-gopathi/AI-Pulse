from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.api.articles_routes import list_homepage_articles
from app.schemas.blog_schemas import HomepageArticleResponse


def test_homepage_articles_returns_latest_ten_without_user_filter():
    articles = [
        SimpleNamespace(
            id=uuid4(),
            title=f"Article {index}",
            summary="Summary",
            url=f"https://example.com/{index}",
            published_at=None,
            technologies=["Python"],
            created_at=datetime.now(timezone.utc),
            chat_id=uuid4(),
        )
        for index in range(10)
    ]

    class FakeScalars:
        def all(self):
            return articles

    class FakeDB:
        statement = None

        def scalars(self, statement):
            self.statement = statement
            return FakeScalars()

    db = FakeDB()
    result = list_homepage_articles(db)

    assert result == articles
    assert db.statement._limit_clause.value == 10
    assert len(db.statement._where_criteria) == 0

    response = HomepageArticleResponse.model_validate(result[0])
    assert response.id == articles[0].id
    assert response.published_at is None
    assert not hasattr(response, "chat_id")
