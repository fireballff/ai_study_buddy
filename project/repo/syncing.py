"""Repository orchestrator that syncs between remote and local stores."""
from __future__ import annotations

from typing import Sequence, Optional
import json

from sqlalchemy import text

from .base import Task, Repository
from .local_sqlite import LocalCacheRepo
from .remote_supabase import RemoteSupabaseRepo


class SyncingRepo(Repository):
    """Repository that delegates to local cache and remote Supabase."""

    def __init__(self, local: LocalCacheRepo, remote: Optional[RemoteSupabaseRepo] = None):
        self.local = local
        self.remote = remote

    # ------------------------------------------------------------------
    def list_tasks(self, filter_mode: str = "All", search: str = "") -> Sequence[Task]:
        return self.local.list_tasks(filter_mode, search)

    # ------------------------------------------------------------------
    def upsert_task(self, task: Task) -> Task:
        if self.remote is not None:
            task = self.remote.upsert_task(task)
            task = self.local.upsert_task(task, dirty=False)
        else:
            task = self.local.upsert_task(task, dirty=True)
            self.local.queue_pending("tasks", "upsert", task.id, task.__dict__)
        return task

    def delete_task(self, local_id: int) -> None:
        if self.remote is not None:
            self.remote.delete_task(local_id)
            self.local.mark_clean(local_id)
        else:
            # mark dirty and queue delete
            self.local.queue_pending("tasks", "delete", local_id, {"id": local_id})
            with self.local.engine.begin() as conn:
                conn.execute(
                    text("UPDATE tasks SET deleted_at=CURRENT_TIMESTAMP, dirty=1 WHERE id=:id"),
                    {"id": local_id},
                )

    # ------------------------------------------------------------------
    def push_pending(self) -> None:
        if self.remote is None:
            return
        for op in self.local.get_pending_ops():
            try:
                if op["op_type"] == "upsert":
                    self.remote.upsert_task(Task(**json.loads(op["payload"])))
                    self.local.mark_clean(int(op["row_local_id"]))
                elif op["op_type"] == "delete":
                    payload = json.loads(op["payload"])
                    self.remote.delete_task(payload["id"])
                self.local.delete_pending_op(op["id"])
            except Exception as exc:  # pragma: no cover - network
                self.local.queue_pending(op["table_name"], op["op_type"], op["row_local_id"], json.loads(op["payload"]))
                break
