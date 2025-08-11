from __future__ import annotations
from datetime import date
from typing import Dict
from PyQt6.QtWidgets import QCalendarWidget
from PyQt6.QtGui import QTextCharFormat
from PyQt6.QtCore import pyqtSignal, QDate


class MonthView(QCalendarWidget):
    """Basic month grid showing counts for each day."""

    day_selected = pyqtSignal(date)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGridVisible(True)
        self.clicked.connect(self._handle_clicked)

    def _handle_clicked(self, qdate: QDate) -> None:
        self.day_selected.emit(qdate.toPyDate())

    def set_badges(self, counts: Dict[date, int]) -> None:
        """Display simple tooltips with item counts for each day."""
        self.clear_badges()
        for day, count in counts.items():
            fmt = QTextCharFormat()
            fmt.setToolTip(f"{count} items")
            qd = QDate(day.year, day.month, day.day)
            self.setDateTextFormat(qd, fmt)

    def clear_badges(self) -> None:
        self.setDateTextFormat(QDate(), QTextCharFormat())
