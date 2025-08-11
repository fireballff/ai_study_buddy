from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout
from PyQt6.QtCore import Qt
from utils.timers import TimerEngine


class TimerWidget(QWidget):
    """UI wrapper around :class:`TimerEngine` with controls."""

    def __init__(self, settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("00:00")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 32px; padding: 16px;")
        layout.addWidget(self.label)

        controls = QHBoxLayout()
        self.mode_box = QComboBox()
        self.mode_box.addItems(["25/5", "50/10"])
        if getattr(settings, "preferred_timer_mode", "25/5") == "50/10":
            self.mode_box.setCurrentText("50/10")
        controls.addWidget(self.mode_box)

        self.start_btn = QPushButton("Start")
        controls.addWidget(self.start_btn)
        self.pause_btn = QPushButton("Pause")
        controls.addWidget(self.pause_btn)
        self.skip_btn = QPushButton("Skip")
        controls.addWidget(self.skip_btn)
        layout.addLayout(controls)

        self.engine = TimerEngine(self.mode_box.currentText())
        self.engine.tick.connect(self.update_label)
        self.mode_box.currentTextChanged.connect(self.change_mode)
        self.start_btn.clicked.connect(self.engine.start)
        self.pause_btn.clicked.connect(self.engine.pause)
        self.skip_btn.clicked.connect(self.engine.skip)

    def change_mode(self, mode: str) -> None:
        self.engine.set_mode(mode)
        if hasattr(self.settings, "preferred_timer_mode"):
            self.settings.preferred_timer_mode = mode

    def update_label(self, remaining: int) -> None:
        minutes = remaining // 60
        seconds = remaining % 60
        self.label.setText(f"{minutes:02d}:{seconds:02d}")
