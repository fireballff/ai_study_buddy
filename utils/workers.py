from __future__ import annotations
from typing import Any
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
import threading
import structlog

from .jobs import JOB_HANDLERS, JobType

class JobRunnable(QRunnable):
    def __init__(self, pool: "WorkerPool", job_type: JobType, payload: Any, attempts: int, backoff: float, delay: float = 0.0):
        super().__init__()
        self.pool = pool
        self.job_type = job_type
        self.payload = payload
        self.attempts = attempts
        self.backoff = backoff
        self.delay = delay

    def run(self) -> None:
        handler = JOB_HANDLERS.get(self.job_type)
        if handler is None:
            self.pool.logger.error("unknown_job", job_type=str(self.job_type))
            return
        try:
            handler(self.payload)
        except Exception as exc:  # pragma: no cover - error handling
            self.pool.logger.error("job_error", job_type=str(self.job_type), exc=str(exc))
            if self.attempts > 1:
                next_delay = self.backoff if self.delay == 0 else self.delay * self.backoff
                timer = threading.Timer(
                    next_delay,
                    lambda: self.pool.pool.start(
                        JobRunnable(self.pool, self.job_type, self.payload, self.attempts - 1, self.backoff, next_delay)
                    ),
                )
                timer.start()
            else:
                self.pool.job_failed.emit(self.job_type, self.payload, exc)

class WorkerPool(QObject):
    job_failed = pyqtSignal(object, object, object)

    def __init__(self, logger: structlog.BoundLogger | None = None):
        super().__init__()
        self.pool = QThreadPool()
        self.logger = logger or structlog.get_logger(__name__)

    def submit(self, job_type: JobType, payload: Any = None, attempts: int = 3, backoff: float = 1.5) -> None:
        runnable = JobRunnable(self, job_type, payload, attempts, backoff)
        self.pool.start(runnable)

worker_pool: WorkerPool | None = None

def init_worker_pool(logger: structlog.BoundLogger | None = None) -> WorkerPool:
    global worker_pool
    if worker_pool is None:
        worker_pool = WorkerPool(logger)
    return worker_pool
