from __future__ import annotations

import pytest
from sqlalchemy import text

from project.db import get_engine, ensure_db
from project.repo.base import Task
from project.repo.local_sqlite import LocalCacheRepo


def test_queue_pending_resolves_id(tmp_path):
    db = tmp_path / "test.db"
    engine = get_engine(str(db))
    ensure_db(engine)
    repo = LocalCacheRepo(engine)

    task = Task(
        id=None,
        owner_user_id=None,
        source="app",
        source_id="abc",
        title="t",
        type="study",
        estimated_duration=1,
    )
    repo.upsert_task(task, dirty=True)
    # queue with missing id; should resolve via source/source_id
    repo.queue_pending("tasks", "upsert", None, task.__dict__)

    with engine.begin() as conn:
        row = conn.execute(text("SELECT row_local_id FROM pending_ops"))
        fetched = row.fetchone()
    assert fetched is not None
    assert int(fetched[0]) == task.id


def test_queue_pending_requires_identifiers(tmp_path):
    db = tmp_path / "test.db"
    engine = get_engine(str(db))
    ensure_db(engine)
    repo = LocalCacheRepo(engine)

    with pytest.raises(ValueError):
        repo.queue_pending("tasks", "upsert", None, {"foo": "bar"})
