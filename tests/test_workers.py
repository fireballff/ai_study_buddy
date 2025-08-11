from __future__ import annotations
import threading
import time
from PyQt6.QtCore import QCoreApplication

from utils.jobs import JobType, JOB_HANDLERS
from utils.workers import WorkerPool


def test_job_runs_off_ui_thread(monkeypatch):
    QCoreApplication([])
    pool = WorkerPool()
    main_thread = threading.get_ident()
    done = threading.Event()
    result: dict[str, int] = {}

    def handler(payload):
        result["thread"] = threading.get_ident()
        done.set()

    monkeypatch.setitem(JOB_HANDLERS, JobType.PLAN_WEEK, handler)
    pool.submit(JobType.PLAN_WEEK)
    assert done.wait(1)
    assert result["thread"] != main_thread


def test_retry_and_backoff_called(monkeypatch):
    QCoreApplication([])
    pool = WorkerPool()
    attempts = {"count": 0}
    done = threading.Event()
    delays: list[float] = []

    def handler(payload):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("boom")
        done.set()

    class InstantTimer:
        def __init__(self, delay, callback):
            delays.append(delay)
            self.callback = callback

        def start(self):
            self.callback()

    monkeypatch.setitem(JOB_HANDLERS, JobType.PLAN_WEEK, handler)
    monkeypatch.setattr("utils.workers.threading.Timer", InstantTimer)
    pool.submit(JobType.PLAN_WEEK, attempts=3, backoff=1.5)
    assert done.wait(1)
    assert attempts["count"] == 3
    assert delays == [1.5, 2.25]
