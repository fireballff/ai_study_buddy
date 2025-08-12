from __future__ import annotations

from datetime import datetime
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .calendar_model import CalendarItem


class HoverCard(QFrame):
    """Small floating card shown when hovering over a calendar item."""

    def __init__(self, engine: Engine, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.engine = engine
        self.setWindowFlags(Qt.WindowType.ToolTip)
        layout = QVBoxLayout(self)
        self.label = QLabel("", self)
        layout.addWidget(self.label)
        self.setStyleSheet("background:#ffffe1; border:1px solid gray;")

    def show_item(self, item: CalendarItem, conflict: bool = False, pos: QPoint | None = None) -> None:
        lines = [item.title]
        course = None
        due = None
        if item.table == "tasks":
            with self.engine.begin() as conn:
                row = conn.execute(
                    text("SELECT course_label, due_date FROM tasks WHERE id=:id"),
                    {"id": item.id},
                ).first()
            if row:
                course = row.course_label
                due = row.due_date
        line2 = item.type
        if course:
            line2 += f" / {course}"
        lines.append(line2)
        lines.append(f"{item.start.strftime('%H:%M')} - {item.end.strftime('%H:%M')}")
        if conflict:
            lines.append("Conflicts")
        if due:
            try:
                due_dt = datetime.fromisoformat(due)
                lines.append(f"Due {due_dt.date().isoformat()}")
            except Exception:
                pass
        self.label.setText("\n".join(lines))
        self.adjustSize()
        if pos is not None:
            self.move(pos)
        self.show()

    def hide_card(self) -> None:
        self.hide()
