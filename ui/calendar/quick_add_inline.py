from __future__ import annotations

import re
from datetime import datetime, timedelta, time, date
from uuid import uuid4
from typing import Optional, Dict, Any, Tuple, Union

try:  # pragma: no cover - used only when Qt is installed
    from PyQt6.QtWidgets import QLineEdit as BaseQLineEdit
    from PyQt6.QtCore import Qt, pyqtSignal, QRect  # type: ignore
    QT_AVAILABLE = True
except Exception:  # pragma: no cover - allows parser tests without Qt libs
    QT_AVAILABLE = False

    class _DummySignal:  # pragma: no cover - simple signal stand-in
        def connect(self, *a, **k):
            pass

        def emit(self, *a, **k):
            pass

    def pyqtSignal(*args, **kwargs):  # type: ignore
        return _DummySignal()

    class BaseQLineEdit:
        def __init__(self, *args, **kwargs):
            self.returnPressed = _DummySignal()

        def hide(self):
            pass

        def show(self):
            pass

        def setGeometry(self, rect):
            pass

        def clear(self):
            pass

        def setFocus(self):
            pass

        def text(self):
            return ""

    class QRect:  # type: ignore
        pass

    class Qt:  # type: ignore
        pass

from sqlalchemy import text
from sqlalchemy.engine import Engine

from agents import classifier

# ----- parsing helpers -----
WEEKDAYS = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

TIME_PATTERN = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", re.IGNORECASE)
DURATION_PATTERN = re.compile(r"(\d+)\s*(h|m)", re.IGNORECASE)


def _next_weekday(start: date, target: int) -> date:
    """Return the next date matching ``target`` weekday.

    ``target`` is an integer where Monday is 0.  If ``start`` already falls on
    the requested weekday the *following* week is returned.  This mirrors the
    semantics users expect when typing things like "@ Mon" while planning later
    in the current week.
    """

    days_ahead = target - start.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start + timedelta(days=days_ahead)


def parse_inline(text: str, default_start: datetime) -> Dict[str, Any]:
    """Parse a quick-add inline string."""
    remaining = text.strip()
    had_at = "@" in remaining
    course: Optional[str] = None

    # extract course label. If preceded by '#', remove it from title
    explicit_course = re.search(r"#([A-Za-z0-9-]+)", remaining)
    if explicit_course:
        c = classifier.extract_course_label(explicit_course.group(1))
        if c:
            course = c
            remaining = remaining.replace(explicit_course.group(0), "")
    else:
        c = classifier.extract_course_label(remaining)
        if isinstance(c, str):
            course = c

    # duration
    duration = 60  # default 1h
    m = DURATION_PATTERN.search(remaining)
    if m:
        amount = int(m.group(1))
        unit = m.group(2).lower()
        duration = amount * 60 if unit == "h" else amount
        remaining = remaining[: m.start()] + remaining[m.end() :]

    # date/time portion
    day = default_start.date()
    tm = default_start.time()
    dt_part = ""
    if "@" in remaining:
        remaining, dt_part = map(str.strip, remaining.split("@", 1))
    else:
        dt_part = remaining.strip()
    if re.search(r"\btomorrow\b", dt_part, re.IGNORECASE):
        day = default_start.date() + timedelta(days=1)
        dt_part = re.sub(r"\btomorrow\b", "", dt_part, flags=re.IGNORECASE)
    for name, idx in WEEKDAYS.items():
        if re.search(rf"\b{name}\b", dt_part, re.IGNORECASE):
            day = _next_weekday(default_start.date(), idx)
            dt_part = re.sub(rf"\b{name}\b", "", dt_part, flags=re.IGNORECASE)
            break
    tm_match = TIME_PATTERN.search(dt_part)
    if tm_match:
        hour = int(tm_match.group(1))
        minute = int(tm_match.group(2) or 0)
        ampm = tm_match.group(3)
        if ampm:
            ampm = ampm.lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            if ampm == "am" and hour == 12:
                hour = 0
        tm = time(hour, minute)
        dt_part = dt_part[: tm_match.start()] + dt_part[tm_match.end() :]
    if not had_at:
        remaining = dt_part
    start_dt = datetime.combine(day, tm)
    end_dt = start_dt + timedelta(minutes=duration)

    # title cleanup
    title = re.sub(r"\s+", " ", remaining).strip()

    cls = classifier.classify(title)
    item_type = cls["type"]
    course = course or cls["course_label"]

    return {
        "title": title,
        "start": start_dt,
        "end": end_dt,
        "type": item_type,
        "course": course,
    }


# ----- widget -----
class QuickAddInline(BaseQLineEdit):
    """Inline quick-add entry displayed over the calendar grid."""

    saved = pyqtSignal()

    def __init__(self, engine: Engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._default_start = datetime.now()
        self.hide()
        self.returnPressed.connect(self.commit)

    def start(
        self,
        rect: Union[QRect, Tuple[int, int, int, int]],
        default_start: datetime,
    ) -> None:
        """Display the inline editor at *rect*.

        ``QLineEdit.setGeometry`` expects a ``QRect`` instance, but call sites may
        provide a simple tuple.  The original implementation attempted to handle
        both but ended up calling ``setGeometry`` with the tuple directly, which
        raises a ``TypeError``.  We now normalise the argument to a ``QRect`` when
        Qt is available.
        """

        if not isinstance(rect, QRect):
            if QT_AVAILABLE:
                rect = QRect(*rect)
            else:  # pragma: no cover - GUI isn't used in tests
                raise TypeError("rect must be a QRect when Qt is unavailable")

        self.setGeometry(rect)
        self._default_start = default_start
        self.clear()
        self.show()
        self.setFocus()

    def commit(self) -> None:
        text = self.text().strip()
        if not text:
            self.hide()
            return
        data = parse_inline(text, self._default_start)
        if data["type"] in {"meeting", "class"}:
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
                    text(
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
