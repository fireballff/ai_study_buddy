from __future__ import annotations
from datetime import datetime, date
from uuid import uuid4
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QTimeEdit,
    QComboBox,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from sqlalchemy import text
from sqlalchemy.engine import Engine


class QuickAddDialog(QDialog):
    """Simple dialog to insert tasks or events."""

    def __init__(self, engine: Engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Quick Add")
        layout = QFormLayout(self)
        self.txt_title = QLineEdit(self)
        self.date = QDateEdit(self)
        self.date.setCalendarPopup(True)
        self.start = QTimeEdit(self)
        self.end = QTimeEdit(self)
        self.cmb_type = QComboBox(self)
        self.cmb_type.addItems(["task", "meeting", "class"])
        self.txt_label = QLineEdit(self)
        layout.addRow("Title", self.txt_title)
        layout.addRow("Date", self.date)
        layout.addRow("Start", self.start)
        layout.addRow("End", self.end)
        layout.addRow("Type", self.cmb_type)
        layout.addRow("Label/Course", self.txt_label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self) -> None:
        title = self.txt_title.text().strip()
        date_val = self.date.date().toPyDate()
        start_time = self.start.time().toPyTime()
        end_time = self.end.time().toPyTime()
        start_dt = datetime.combine(date_val, start_time)
        end_dt = datetime.combine(date_val, end_time)
        typ = self.cmb_type.currentText()
        label = self.txt_label.text().strip() or None
        if typ in {"meeting", "class"}:
            with self.engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO events (source, source_id, title, start_time, end_time, type, description)
                        VALUES (:source, :source_id, :title, :start, :end, :type, '')
                        """
                    ),
                    {
                        "source": "app",
                        "source_id": uuid4().hex,
                        "title": title,
                        "start": start_dt.isoformat(),
                        "end": end_dt.isoformat(),
                        "type": typ,
                    },
                )
        else:
            duration = int((end_dt - start_dt).total_seconds() // 60)
            if duration <= 0:
                duration = 60
            with self.engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO tasks (title, type, estimated_duration, due_date, course_label, start_time, end_time)
                        VALUES (:title, :type, :est, NULL, :label, :start, :end)
                        """
                    ),
                    {
                        "title": title,
                        "type": typ,
                        "est": duration,
                        "label": label,
                        "start": start_dt.isoformat(),
                        "end": end_dt.isoformat(),
                    },
                )
        super().accept()
