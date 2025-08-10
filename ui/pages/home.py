from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class HomePage(QWidget):
    """
    Landing page for the AI Study Buddy app.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Welcome to AI Study Buddy")
        title.setObjectName("page-title")
        layout.addWidget(title)
        subtitle = QLabel("Connect your calendar and start planning smarter.")
        subtitle.setStyleSheet("margin-bottom: 8px;")
        layout.addWidget(subtitle)
        layout.addStretch(1)