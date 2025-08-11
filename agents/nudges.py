from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict


def generate_nudges(
    planned_sessions: List[Dict],
    tasks: List[Dict],
    *,
    max_sessions_per_day: int = 4,
    now: datetime | None = None,
) -> List[str]:
    """Return up to three rule-based nudges.

    Parameters
    ----------
    planned_sessions: List of scheduled study blocks.
    tasks: Original tasks including tests with due dates.
    max_sessions_per_day: Threshold for recommending spreading tasks.
    now: Optional reference time for determinism in tests.
    """
    now = now or datetime.now()
    nudges: List[str] = []

    # Rule 1: Upcoming tests within 72h with less than 2h of study scheduled.
    cutoff = now + timedelta(hours=72)
    tests_due = [
        t for t in tasks
        if t.get("type") == "test"
        and t.get("due_date")
        and now <= t["due_date"] <= cutoff
    ]
    for test in tests_due:
        course = test.get("course") or test.get("title")
        study_minutes = 0
        for sess in planned_sessions:
            if sess.get("course") == course:
                study_minutes += (sess["end_time"] - sess["start_time"]).total_seconds() / 60
        if study_minutes < 120:
            nudges.append(f"Add at least one 50-minute session for {course}.")
        if len(nudges) >= 3:
            return nudges[:3]

    # Sessions scheduled today
    today = now.date()
    todays_sessions = [s for s in planned_sessions if s["start_time"].date() == today]

    # Rule 2: Too many sessions today
    if len(todays_sessions) > max_sessions_per_day:
        task_title = todays_sessions[-1].get("title", "a task")
        nudges.append(f"Consider spreading {task_title} to tomorrow.")
        if len(nudges) >= 3:
            return nudges[:3]

    # Rule 3: Long day
    if len(todays_sessions) >= 5:
        nudges.append("Plan a 10-minute break after each session.")

    return nudges[:3]
