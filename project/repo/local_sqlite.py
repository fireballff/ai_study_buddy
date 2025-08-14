"""Local SQLite cache repository."""
from __future__ import annotations

from typing import Sequence, List
from datetime import datetime
import json
import uuid

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .base import Task
from .query_builders import build_tasks_query


class LocalCacheRepo:
    """Repository backed by the local SQLite cache."""

    def __init__(self, engine: Engine):
        self.engine = engine

    # ------------------------------------------------------------------
    def list_tasks(self, filter_mode: str = "All", search: str = "") -> Sequence[Task]:
        sql, params = build_tasks_query(filter_mode, search, include_sync_columns=True)
        with self.engine.begin() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
            return [Task(**row) for row in rows]

    # ------------------------------------------------------------------
    def upsert_task(self, task: Task, dirty: bool = False) -> Task:
        updated_at = datetime.utcnow().isoformat()
        version = str(uuid.uuid4())
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO tasks (
                        id, owner_user_id, source, source_id, title, type, estimated_duration,
                        due_date, state, start_time, end_time, course_label, priority,
                        updated_at, version, dirty
                    ) VALUES (
                        :id, :owner_user_id, :source, :source_id, :title, :type, :estimated_duration,
                        :due_date, :state, :start_time, :end_time, :course_label, :priority,
                        :updated_at, :version, :dirty
                    )
                    ON CONFLICT(id) DO UPDATE SET
                        owner_user_id=excluded.owner_user_id,
                        source=excluded.source,
                        source_id=excluded.source_id,
                        title=excluded.title,
                        type=excluded.type,
                        estimated_duration=excluded.estimated_duration,
                        due_date=excluded.due_date,
                        state=excluded.state,
                        start_time=excluded.start_time,
                        end_time=excluded.end_time,
                        course_label=excluded.course_label,
                        priority=excluded.priority,
                        updated_at=excluded.updated_at,
                        version=excluded.version,
                        dirty=excluded.dirty
                    """
                ),
                {
                    "id": task.id,
                    "owner_user_id": task.owner_user_id,
                    "source": task.source,
                    "source_id": task.source_id,
                    "title": task.title,
                    "type": task.type,
                    "estimated_duration": task.estimated_duration,
                    "due_date": task.due_date,
                    "state": task.state,
                    "start_time": task.start_time,
                    "end_time": task.end_time,
                    "course_label": task.course_label,
                    "priority": task.priority,
                    "updated_at": updated_at,
                    "version": version,
                    "dirty": int(dirty),
                },
            )
            if task.id is None:
                row = conn.execute(
                    text(
                        "SELECT id FROM tasks WHERE source=:source AND source_id=:source_id"
                    ),
                    {"source": task.source, "source_id": task.source_id},
                ).fetchone()
                task.id = row[0]
        task.updated_at = updated_at
        task.version = version
        task.dirty = int(dirty)
        return task

    # ------------------------------------------------------------------
    def queue_pending(self, table: str, op_type: str, row_local_id: int, payload: dict) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO pending_ops (table_name, op_type, row_local_id, payload) VALUES (:t,:o,:r,:p)"
                ),
                {"t": table, "o": op_type, "r": row_local_id, "p": json.dumps(payload)},
            )

    def get_pending_ops(self) -> List[dict]:
        with self.engine.begin() as conn:
            rows = conn.execute(text("SELECT * FROM pending_ops ORDER BY id")).mappings().all()
            return [dict(r) for r in rows]

    def delete_pending_op(self, op_id: int) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM pending_ops WHERE id=:id"), {"id": op_id})

    # ------------------------------------------------------------------
    def mark_clean(self, local_id: int) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text("UPDATE tasks SET dirty=0 WHERE id=:id"), {"id": local_id}
            )
