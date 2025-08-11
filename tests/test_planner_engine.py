from __future__ import annotations
from datetime import datetime, time, timedelta

from agents.planner_engine import schedule
from project.prefs import UserPrefs


def _prefs():
    return UserPrefs(day_start=time(8, 0), day_end=time(12, 0), default_session_minutes=60, max_sessions_per_day=2)


def test_respects_events_and_blocks():
    base = datetime(2024, 1, 1, 8, 0)
    tasks = [
        {"id": 1, "title": "Task", "estimated_duration": 60, "due_date": base + timedelta(days=1), "priority": 1, "state": "pending"}
    ]
    events = [
        {"start_time": base.replace(hour=9), "end_time": base.replace(hour=10), "title": "Meeting"},
    ]
    blocks = [
        {"kind": "busy", "start_time": base.replace(hour=8), "end_time": base.replace(hour=9)},
        {"kind": "busy", "start_time": base.replace(hour=10), "end_time": base.replace(hour=11)},
        {"kind": "study_window", "start_time": base.replace(hour=8), "end_time": base.replace(hour=12)},
    ]
    sessions = schedule(tasks, events, blocks, _prefs(), start=base)
    assert sessions[0]["start_time"] == base.replace(hour=11)
    assert sessions[0]["end_time"] == base.replace(hour=12)


def test_deadline_before_window_pushes_up_priority():
    base = datetime(2024, 1, 1, 8, 0)
    tasks = [
        {"id": 1, "title": "Later", "estimated_duration": 60, "due_date": base + timedelta(days=3), "priority": 1, "state": "pending"},
        {"id": 2, "title": "Soon", "estimated_duration": 60, "due_date": base + timedelta(days=1), "priority": 5, "state": "pending"},
    ]
    sessions = schedule(tasks, [], [], _prefs(), start=base)
    assert sessions[0]["task_id"] == 2


def test_splits_into_sessions_and_limits_per_day():
    base = datetime(2024, 1, 1, 8, 0)
    tasks = [
        {"id": 1, "title": "Big", "estimated_duration": 180, "due_date": base + timedelta(days=3), "priority": 1, "state": "pending"}
    ]
    sessions = schedule(tasks, [], [], _prefs(), start=base)
    assert len(sessions) == 3
    assert sessions[0]["start_time"] == base.replace(hour=8)
    assert sessions[1]["start_time"] == base.replace(hour=9)
    # third session on next day 8am
    assert sessions[2]["start_time"] == base.replace(day=2, hour=8)


def test_does_not_schedule_past_due():
    base = datetime(2024, 1, 1, 8, 0)
    tasks = [
        {"id": 1, "title": "DueEarly", "estimated_duration": 150, "due_date": base.replace(hour=9, minute=30), "priority": 1, "state": "pending"}
    ]
    sessions = schedule(tasks, [], [], _prefs(), start=base)
    # Total scheduled time should end exactly at due date
    assert sessions[-1]["end_time"] <= base.replace(hour=9, minute=30)
