from __future__ import annotations

from datetime import datetime

from project.db import get_engine, ensure_db
from sqlalchemy import text


def _setup_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = get_engine(str(db_path))
    ensure_db(engine)
    return engine


def test_create_task_with_due_date(tmp_path):
    engine = _setup_engine(tmp_path)
    due = datetime(2024, 1, 1, 12, 0)
    due_iso = due.isoformat()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO tasks (title, type, estimated_duration, due_date) VALUES (:title, :type, :duration, :due)"
            ),
            {"title": "task", "type": "homework", "duration": 60, "due": due_iso},
        )
        row = conn.execute(text("SELECT due_date FROM tasks")).fetchone()
        assert row is not None
        assert row.due_date == due_iso


def test_create_task_without_due_date(tmp_path):
    engine = _setup_engine(tmp_path)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO tasks (title, type, estimated_duration, due_date) VALUES (:title, :type, :duration, :due)"
            ),
            {"title": "task", "type": "homework", "duration": 60, "due": None},
        )
        row = conn.execute(text("SELECT due_date FROM tasks")).fetchone()
        assert row is not None
        assert row.due_date is None

