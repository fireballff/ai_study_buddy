from __future__ import annotations
from datetime import datetime, timedelta, time
import importlib

from agents.nudges import generate_nudges


NOW = datetime(2024, 1, 1, 9, 0)


def make_session(start_offset_minutes: int, course: str | None = None, title: str | None = None):
    start = NOW + timedelta(minutes=start_offset_minutes)
    end = start + timedelta(minutes=50)
    return {
        'id': start_offset_minutes,
        'title': title or f'Task {start_offset_minutes}',
        'start_time': start,
        'end_time': end,
        'course': course,
    }


def test_nudge_for_upcoming_test():
    tasks = [{
        'id': 1,
        'title': 'Math Exam',
        'type': 'test',
        'course': 'Math',
        'due_date': NOW + timedelta(hours=48),
    }]
    planned = [make_session(0, course='Math')]
    nudges = generate_nudges(planned, tasks, now=NOW)
    assert "Add at least one 50-minute session for Math." in nudges


def test_nudge_for_over_scheduled_day():
    planned = [make_session(i * 60) for i in range(4)]
    nudges = generate_nudges(planned, [], max_sessions_per_day=3, now=NOW)
    assert nudges == ["Consider spreading Task 180 to tomorrow."]


def test_nudge_for_long_day():
    planned = [make_session(i * 60) for i in range(5)]
    nudges = generate_nudges(planned, [], now=NOW)
    assert "Plan a 10-minute break after each session." in nudges


def test_planner_returns_nudges_when_enabled(monkeypatch):
    monkeypatch.setenv('ENABLE_MICRO_COACHING', 'true')
    import agents.planner as planner
    importlib.reload(planner)
    tasks = [
        {'id': i, 'title': f'Task {i}', 'type': 'study', 'estimated_duration': 50, 'due_date': None}
        for i in range(5)
    ]
    scheduled, nudges = planner.schedule_tasks(tasks, [], work_start=time(9, 0), work_end=time(15, 0))
    assert "Plan a 10-minute break after each session." in nudges
    monkeypatch.delenv('ENABLE_MICRO_COACHING', raising=False)
    importlib.reload(planner)
