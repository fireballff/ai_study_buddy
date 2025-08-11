from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import text

from .db import get_engine
from .settings import load_settings

ALPHA = 0.3


def _engine():
    settings = load_settings()
    return get_engine(settings.sqlite_path)


def record_session(
    task_id: int,
    planned_minutes: int,
    actual_minutes: int,
    task_type: str,
    course_label: Optional[str],
    timestamp: Optional[datetime] = None,
) -> None:
    """Record a completed study session."""
    ts = (timestamp or datetime.utcnow()).isoformat()
    engine = _engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO session_log (task_id, planned_minutes, actual_minutes, type, course_label, logged_at)
                VALUES (:task_id, :planned, :actual, :type, :course, :ts)
                """
            ),
            {
                "task_id": task_id,
                "planned": planned_minutes,
                "actual": actual_minutes,
                "type": task_type,
                "course": course_label,
                "ts": ts,
            },
        )


def get_estimate(task_type: Optional[str], course_label: Optional[str], default_minutes: int) -> int:
    """Return EWMA estimate for session minutes."""
    engine = _engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT actual_minutes FROM session_log
                WHERE type = :type
                  AND ((course_label = :course) OR (course_label IS NULL AND :course IS NULL))
                ORDER BY logged_at
                """
            ),
            {"type": task_type, "course": course_label},
        ).fetchall()
    estimate = float(default_minutes)
    for r in rows:
        estimate = ALPHA * float(r.actual_minutes) + (1 - ALPHA) * estimate
    return int(round(estimate))
