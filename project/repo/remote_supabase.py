"""Remote repository backed by Supabase."""
from __future__ import annotations

from typing import Sequence

from .base import Task
from integrations.supabase_client import SupabaseClient


class RemoteSupabaseRepo:
    def __init__(self, client: SupabaseClient):
        self.client = client

    def list_tasks(self, filter_mode: str = "All", search: str = "") -> Sequence[Task]:
        data = self.client.select("tasks", "*")
        return [Task(**row) for row in data]

    def upsert_task(self, task: Task) -> Task:
        payload = task.__dict__.copy()
        self.client.upsert("tasks", payload)
        task.dirty = 0
        return task

    def delete_task(self, local_id: int) -> None:
        self.client.delete("tasks", "id", local_id)

    def push_pending(self) -> None:  # pragma: no cover - remote is authoritative
        pass
