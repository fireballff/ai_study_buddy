from __future__ import annotations
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class TimerEngine(QObject):
    """Simple Pomodoro-like timer engine based on QTimer.

    Supports two modes: "25/5" and "50/10" where the numbers denote
    work and break durations in minutes. The engine emits signals on
    phase transitions and every tick. Designed to avoid blocking the UI
    thread; QTimer drives the countdown.
    """

    tick = pyqtSignal(int)  # remaining seconds
    session_started = pyqtSignal()
    session_finished = pyqtSignal()
    break_started = pyqtSignal()
    break_finished = pyqtSignal()

    def __init__(self, mode: str = "25/5", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.mode = mode
        self.work_duration, self.break_duration = self._durations_for_mode(mode)
        self.phase: str = "idle"  # "work", "break", "idle"
        self.remaining: int = 0
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

    def _durations_for_mode(self, mode: str) -> tuple[int, int]:
        if mode == "50/10":
            return 50 * 60, 10 * 60
        # default to 25/5
        return 25 * 60, 5 * 60

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.work_duration, self.break_duration = self._durations_for_mode(mode)

    def start(self) -> None:
        """Begin a work session."""
        self.phase = "work"
        self.remaining = self.work_duration
        self.session_started.emit()
        self.tick.emit(self.remaining)
        self.timer.start()

    def pause(self) -> None:
        self.timer.stop()

    def resume(self) -> None:
        if self.phase != "idle":
            self.timer.start()

    def skip(self) -> None:
        """Skip the current phase immediately."""
        self.remaining = 0
        self._tick()  # force transition

    # Exposed for tests to advance time manually
    def tick_manual(self) -> None:
        self._tick()

    def _tick(self) -> None:
        if self.phase == "idle":
            return
        self.remaining -= 1
        if self.remaining <= 0:
            if self.phase == "work":
                self.session_finished.emit()
                self.phase = "break"
                self.remaining = self.break_duration
                self.break_started.emit()
            elif self.phase == "break":
                self.break_finished.emit()
                self.phase = "work"
                self.remaining = self.work_duration
                self.session_started.emit()
        self.tick.emit(self.remaining)
