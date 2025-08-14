from __future__ import annotations

from project.db import get_engine, ensure_db
from project.repo.local_sqlite import LocalCacheRepo
from project.repo.remote_supabase import RemoteSupabaseRepo
from project.repo.syncing import SyncingRepo
from project.repo.base import Task


class DummyRemote(RemoteSupabaseRepo):
    def __init__(self):
        self.upserts = []

    def upsert_task(self, task: Task) -> Task:  # type: ignore[override]
        self.upserts.append(task)
        task.dirty = 0
        return task

    def delete_task(self, local_id: int) -> None:  # pragma: no cover - not used
        pass


def test_offline_queue_and_push(tmp_path):
    engine = get_engine(str(tmp_path / "db.sqlite"))
    ensure_db(engine)
    local = LocalCacheRepo(engine)
    repo = SyncingRepo(local, remote=None)
    task = Task(
        id=None,
        owner_user_id="user1",
        source="app",
        source_id="t1",
        title="Study",
        type="study",
        estimated_duration=60,
    )
    repo.upsert_task(task)
    # should be marked dirty and queued
    tasks = local.list_tasks()
    assert tasks[0].dirty == 1
    assert local.get_pending_ops()
    # switch to online and push
    remote = DummyRemote()
    repo.remote = remote
    repo.push_pending()
    assert len(remote.upserts) == 1
    assert not local.get_pending_ops()
    tasks = local.list_tasks()
    assert tasks[0].dirty == 0
