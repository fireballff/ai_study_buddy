"""Background syncing engine."""
from __future__ import annotations

import threading
import time
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from project.repo.syncing import SyncingRepo


class SyncEngine(QObject):
    """Runs pull/push sync in a background thread."""

    sync_started = pyqtSignal()
    sync_finished = pyqtSignal()
    sync_error = pyqtSignal(str)

    def __init__(self, repo: SyncingRepo, interval: float = 30.0):
        super().__init__()
        self.repo = repo
        self.interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join()
        self._thread = None

    # ------------------------------------------------------------------
    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.sync_started.emit()
                self.repo.push_pending()
                self.sync_finished.emit()
            except Exception as exc:  # pragma: no cover - background
                self.sync_error.emit(str(exc))
            self._stop.wait(self.interval)
