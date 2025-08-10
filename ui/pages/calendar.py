from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class CalendarPage(QWidget):
    """
    Calendar page that will display events and scheduled tasks in week/month view.
    In this milestone, it shows a placeholder message.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Calendar")
        title.setObjectName("page-title")
        layout.addWidget(title)
        subtitle = QLabel("Week and month views with drag & drop will appear here in later milestones.")
        layout.addWidget(subtitle)
        layout.addStretch(1)