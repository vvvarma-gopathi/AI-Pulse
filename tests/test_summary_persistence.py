from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from app.ingestion.summerization import save_article_summaries


def test_article_summary_integrity_error_is_rolled_back_and_raised():
    chat_id = uuid4()

    class FailingDB:
        rolled_back = False

        calls = 0

        def execute(self, _statement):
            self.calls += 1
            if self.calls == 1:
                return SimpleNamespace(
                    scalar_one_or_none=lambda: SimpleNamespace(id=chat_id)
                )
            raise IntegrityError(
                "insert article summary",
                {},
                Exception("database unavailable"),
            )

        def commit(self):
            pass

        def rollback(self):
            self.rolled_back = True

    db = FailingDB()
    article = SimpleNamespace(
        title="Research article",
        summary="A useful summary",
        url="https://example.test/article",
        published_at=None,
        technologies=["Python"],
    )

    try:
        save_article_summaries(chat_id, [article], db)
    except IntegrityError:
        pass
    else:
        raise AssertionError("Database integrity failures must be raised")

    assert db.rolled_back


def test_duplicate_urls_in_a_chat_are_inserted_once_conflict_safely():
    chat_id = uuid4()
    url = "https://example.test/article"

    class FakeDB:
        statement = None

        def execute(self, statement):
            if self.statement is None:
                self.statement = statement
                return SimpleNamespace(
                    scalar_one_or_none=lambda: SimpleNamespace(id=chat_id)
                )
            self.statement = statement
            return SimpleNamespace(rowcount=1)

        def commit(self):
            pass

        def rollback(self):
            raise AssertionError("No rollback expected")

    db = FakeDB()
    article = SimpleNamespace(
        title="Research article",
        summary="A useful summary",
        url=url,
        published_at=None,
        technologies=["Python"],
    )

    inserted = save_article_summaries(
        chat_id,
        [article, article],
        db,
    )

    compiled = db.statement.compile(dialect=postgresql.dialect())
    url_values = [
        value
        for key, value in compiled.params.items()
        if key.startswith("url")
    ]

    assert inserted == 1
    assert url_values == [url]
    assert (
        "ON CONFLICT ON CONSTRAINT uq_article_summaries_chat_url DO NOTHING"
        in str(compiled)
    )
