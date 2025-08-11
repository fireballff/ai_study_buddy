from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class FocusTimeline(QWidget):
    """Simple timeline showing the current and next three sessions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title = QLabel("Focus Timeline")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        self.blocks: list[QLabel] = []
        for _ in range(4):
            lbl = QLabel("–")
            lbl.setStyleSheet("font-size: 16px; padding: 8px;")
            layout.addWidget(lbl)
            self.blocks.append(lbl)

    def set_sessions(self, sessions: list[str]) -> None:
        for i, text in enumerate(sessions[:4]):
            self.blocks[i].setText(text)
        for j in range(len(sessions), 4):
            self.blocks[j].setText("–")
