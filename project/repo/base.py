"""Repository data structures and protocol interfaces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, Optional


@dataclass
class Task:
    """Represents a task record."""

    id: Optional[int]  # local autoincrement id
    owner_user_id: Optional[str]
    source: str
    source_id: str
    title: str
    type: str
    estimated_duration: int
    due_date: Optional[str] = None
    state: str = "pending"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    course_label: Optional[str] = None
    priority: int = 0
    updated_at: Optional[str] = None
    version: Optional[str] = None
    dirty: int = 0


class Repository(Protocol):
    """Interface for task and event repositories."""

    # Tasks
    def list_tasks(self, filter_mode: str = "All", search: str = "") -> Sequence[Task]: ...

    def upsert_task(self, task: Task) -> Task: ...

    def delete_task(self, local_id: int) -> None: ...

    def push_pending(self) -> None: ...
