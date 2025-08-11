from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt


class OneThingNow(QWidget):
    """Displays the current task with basic controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label = QLabel("One thing now")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 20px; padding: 16px;")
        layout.addWidget(self.label)

        controls = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        controls.addWidget(self.start_btn)
        self.pause_btn = QPushButton("Pause")
        controls.addWidget(self.pause_btn)
        self.skip_btn = QPushButton("Skip")
        controls.addWidget(self.skip_btn)
        layout.addLayout(controls)
