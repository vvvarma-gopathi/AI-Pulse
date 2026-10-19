from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import projects_routes
from app.models.projects import ProjectDocumentChunk
from app.rag import indexing_service
from app.schemas.projects import ProjectWrite


class FakeBackgroundTasks:
    def __init__(self):
        self.tasks = []

    def add_task(self, function, *args):
        self.tasks.append((function, args))


class FakeProjectDB:
    def __init__(self):
        self.project = None
        self.deleted = []
        self.executed = []

    def add(self, project):
        project.id = project.id or uuid4()
        project.created_at = datetime.now(timezone.utc)
        project.updated_at = datetime.now(timezone.utc)
        self.project = project

    def scalar(self, _statement):
        return self.project

    def commit(self):
        pass

    def refresh(self, _project):
        pass

    def execute(self, statement):
        self.executed.append(statement)

    def delete(self, project):
        self.deleted.append(project)


def test_project_create_and_update_schedule_indexing():
    db = FakeProjectDB()
    background_tasks = FakeBackgroundTasks()
    user = SimpleNamespace(id=uuid4())
    project_input = ProjectWrite(
        name="A project",
        description="A project description",
        technologies=["Python"],
    )

    created = projects_routes.create_project(
        project_input,
        background_tasks,
        user,
        db,
    )
    assert created.user_id == user.id
    assert created.indexing_status == "pending"
    assert background_tasks.tasks[-1] == (
        indexing_service.index_project_background,
        (created.id, user.id),
    )

    updated = projects_routes.update_project(
        created.id,
        ProjectWrite(
            name="Updated project",
            description="Updated description",
            technologies=["Python", "PostgreSQL"],
        ),
        background_tasks,
        user,
        db,
    )
    assert updated.name == "Updated project"
    assert updated.indexing_status == "pending"
    assert len(background_tasks.tasks) == 2


def test_project_chunk_ids_are_deterministic_on_reindex(monkeypatch):
    project = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        name="Project",
        description="A description that is long enough to make chunks.",
        technologies=["Python"],
        goals=["Reduce manual work"],
        capabilities=["Analyze data"],
        limitations=["Early prototype"],
        status="active",
        updated_at=datetime.now(timezone.utc),
        indexing_status="pending",
    )
    monkeypatch.setattr(
        indexing_service,
        "embed_texts",
        lambda chunks: [[0.1] * 768 for _ in chunks],
    )

    class FakeDB:
        def __init__(self):
            self.added = []
            self.deletes = 0

        def execute(self, _statement):
            self.deletes += 1

        def add(self, chunk):
            self.added.append(chunk)

        def commit(self):
            pass

        def rollback(self):
            pass

    first_db = FakeDB()
    second_db = FakeDB()
    indexing_service.index_project(first_db, project)
    indexing_service.index_project(second_db, project)

    assert [chunk.id for chunk in first_db.added] == [
        chunk.id for chunk in second_db.added
    ]
    assert first_db.deletes == second_db.deletes == 1
    assert all(chunk.user_id == project.user_id for chunk in first_db.added)
    assert all(chunk.source_id == project.id for chunk in first_db.added)


def test_embedding_failure_preserves_project_and_marks_index_failed(
    monkeypatch,
):
    project = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        name="Project",
        description="A description",
        technologies=[],
        goals=[],
        capabilities=[],
        limitations=[],
        status="active",
        updated_at=datetime.now(timezone.utc),
        indexing_status="pending",
    )

    class FakeDB:
        def scalar(self, _statement):
            return project

        def rollback(self):
            pass

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        "core.database.SessionLocal",
        lambda: FakeDB(),
    )
    monkeypatch.setattr(
        indexing_service,
        "embed_texts",
        lambda _texts: (_ for _ in ()).throw(RuntimeError("provider down")),
    )

    indexing_service.index_project_background(
        project.id,
        project.user_id,
    )

    assert project.indexing_status == "failed"


def test_project_deletion_cascades_to_vector_chunks():
    foreign_key = next(
        iter(ProjectDocumentChunk.__table__.c.project_id.foreign_keys)
    )
    assert foreign_key.ondelete == "CASCADE"


def test_project_delete_removes_chunks_with_owner_filter():
    db = FakeProjectDB()
    user = SimpleNamespace(id=uuid4())
    project = SimpleNamespace(id=uuid4(), user_id=user.id)
    db.project = project

    projects_routes.delete_project(project.id, user, db)

    assert len(db.executed) == 1
    assert db.deleted == [project]
