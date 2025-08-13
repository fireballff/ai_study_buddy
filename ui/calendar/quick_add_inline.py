from __future__ import annotations

import re
from datetime import datetime, timedelta, time, date
from typing import Optional, Dict, Any
from uuid import uuid4

from PyQt6.QtCore import pyqtSignal, QRect
from PyQt6.QtWidgets import QLineEdit

from sqlalchemy import text as sql_text
from sqlalchemy.engine import Engine

from agents import classifier

# ----- parsing helpers -----
WEEKDAYS: Dict[str, int] = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
}

TIME_PATTERN = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", re.IGNORECASE)
DURATION_PATTERN = re.compile(r"(\d+)\s*(h|m)", re.IGNORECASE)


def _next_weekday(start: date, target: int) -> date:
    days_ahead = target - start.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start + timedelta(days=days_ahead)


def parse_inline(text: str, default_start: datetime) -> Dict[str, Any]:
    """
    Parse a natural-language quick-add line into a structured payload.

    Examples:
        "Math HW @ tue 4pm 90m #MATH101"
        "Study physics tomorrow 2h"
        "review notes wed 7:30pm #PHY"
    """
    remaining = text.strip()
    had_at = "@" in remaining
    course: Optional[str] = None

    # explicit course label with '#'
    explicit_course = re.search(r"#([A-Za-z0-9-]+)", remaining)
    if explicit_course:
        c = classifier.extract_course_label(explicit_course.group(1))
        if isinstance(c, str):
            course = c
            remaining = remaining.replace(explicit_course.group(0), "")
    else:
        c = classifier.extract_course_label(remaining)
        if isinstance(c, str):
            course = c

    # duration (default 60m)
    duration = 60
    m = DURATION_PATTERN.search(remaining)
    if m:
        amount = int(m.group(1))
        unit = m.group(2).lower()
        duration = amount * 60 if unit == "h" else amount
        remaining = remaining[: m.start()] + remaining[m.end():]

    # date/time parts
    day = default_start.date()
    tm = default_start.time()
    if "@" in remaining:
        remaining, dt_part = remaining.split("@", 1)
    else:
        dt_part = remaining

    # keywords: tomorrow / weekdays
    if re.search(r"\btomorrow\b", dt_part, re.IGNORECASE):
        day = default_start.date() + timedelta(days=1)
        dt_part = re.sub(r"\btomorrow\b", "", dt_part, flags=re.IGNORECASE)

    for name, idx in WEEKDAYS.items():
        if re.search(rf"\b{name}\b", dt_part, re.IGNORECASE):
            day = _next_weekday(default_start.date(), idx)
            dt_part = re.sub(rf"\b{name}\b", "", dt_part, flags=re.IGNORECASE)
            break

    # explicit time like "4pm", "7:30", "19:05", etc.
    tm_match = TIME_PATTERN.search(dt_part)
    if tm_match:
        hour = int(tm_match.group(1))
        minute = int(tm_match.group(2) or 0)
        ampm = (tm_match.group(3) or "").lower()
        if ampm == "pm" and hour != 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        tm = time(hour, minute)
        dt_part = dt_part[: tm_match.start()] + dt_part[tm_match.end():]

    # if no explicit "@", fold residual dt_part back into title
    if not had_at:
        remaining = dt_part

    start_dt = datetime.combine(day, tm)
    end_dt = start_dt + timedelta(minutes=duration)

    # title cleanup
    title = re.sub(r"\s+", " ", remaining).strip()

    # classify (defensive defaults)
    cls = classifier.classify(title) or {}
    item_type = cls.get("type", "task")
    val = cls.get("course_label")
    if isinstance(val, str) and course is None:
        course = val

    return {
        "title": title,
        "start": start_dt,
        "end": end_dt,
        "type": item_type,
        "course": course,
    }


# ----- widget -----
class BaseQLineEdit(QLineEdit):
    """Thin wrapper for clarity/extension."""
    pass


class QuickAddInline(BaseQLineEdit):
    """Inline quick-add entry displayed over the calendar grid."""

    saved = pyqtSignal()

    def __init__(self, engine: Engine, parent=None) -> None:
        super().__init__(parent)
        self.engine = engine
        self._default_start: datetime = datetime.now()
        self.hide()
        self.returnPressed.connect(self.commit)

    def start(self, rect: QRect, default_start: datetime) -> None:
        self.setGeometry(rect)
        self._default_start = default_start
        self.clear()
        self.show()
        self.setFocus()

    def commit(self) -> None:
        input_text = self.text().strip()
        if not input_text:
            self.hide()
            return

        data = parse_inline(input_text, self._default_start)

        if data["type"] in {"meeting", "class"}:
            with self.engine.begin() as conn:
                conn.execute(
                    sql_text(
                        """
                        INSERT INTO events (source, source_id, title, start_time, end_time, type, description)
                        VALUES (:source, :source_id, :title, :start, :end, :type, '')
                        """
                    ),
                    {
                        "source": "app",
                        "source_id": uuid4().hex,
                        "title": data["title"],
                        "start": data["start"].isoformat(),
                        "end": data["end"].isoformat(),
                        "type": data["type"],
                    },
                )
        else:
            duration = int((data["end"] - data["start"]).total_seconds() // 60)
            with self.engine.begin() as conn:
                conn.execute(
                    sql_text(
                        """
                        INSERT INTO tasks (title, type, estimated_duration, due_date, course_label, start_time, end_time)
                        VALUES (:title, :type, :est, NULL, :label, :start, :end)
                        """
                    ),
                    {
                        "title": data["title"],
                        "type": data["type"],
                        "est": duration,
                        "label": data["course"],
                        "start": data["start"].isoformat(),
                        "end": data["end"].isoformat(),
                    },
                )

        self.hide()
        self.saved.emit()
