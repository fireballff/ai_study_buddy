from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal


class Sidebar(QWidget):
    """
    Vertical navigation sidebar with fixed width. Emits a 'navigate' signal when buttons are clicked.
    """
    navigate = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        def add_btn(key: str, label: str):
            btn = QPushButton(label)
            btn.setObjectName(f"nav-{key}")
            btn.setMinimumHeight(44)
            btn.clicked.connect(lambda: self.navigate.emit(key))
            layout.addWidget(btn)

        add_btn("home", "Home")
        add_btn("calendar", "Calendar")
        add_btn("tasks", "Tasks")
        add_btn("planner", "Planner")
        add_btn("settings", "Settings")
        add_btn("adhd", "Focus Mode")
        layout.addStretch(1)