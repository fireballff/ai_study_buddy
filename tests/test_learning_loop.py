from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import text

from project.db import get_engine, ensure_db
from project.prefs import UserPrefs
from project import metrics
from agents import planner_engine


def _init_db(tmp_path):
    db_path = tmp_path / "test.db"
    engine = get_engine(str(db_path))
    ensure_db(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE session_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    planned_minutes INTEGER NOT NULL,
                    actual_minutes INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    course_label TEXT,
                    logged_at TEXT NOT NULL
                )
                """
            )
        )
    return engine, db_path


def _settings(db_path, flag: bool):
    class S:
        sqlite_path = str(db_path)
        enable_learning_loop = flag
    return S()


def test_record_session_logs(tmp_path, monkeypatch):
    engine, db_path = _init_db(tmp_path)
    settings = _settings(db_path, True)
    monkeypatch.setattr(metrics, "load_settings", lambda: settings)
    metrics.record_session(1, 50, 40, "study", "math")
    with engine.begin() as conn:
        row = conn.execute(text("SELECT task_id, planned_minutes, actual_minutes, type, course_label FROM session_log"))
        rec = row.fetchone()
        assert rec.task_id == 1
        assert rec.planned_minutes == 50
        assert rec.actual_minutes == 40
        assert rec.type == "study"
        assert rec.course_label == "math"


def test_planner_uses_adjusted_estimate(tmp_path, monkeypatch):
    engine, db_path = _init_db(tmp_path)
    settings = _settings(db_path, True)
    monkeypatch.setattr(metrics, "load_settings", lambda: settings)
    monkeypatch.setattr(planner_engine, "load_settings", lambda: settings)
    metrics.record_session(1, 50, 30, "study", "math")
    tasks = [{"id": 1, "title": "T", "type": "study", "course_label": "math", "estimated_duration": 60}]
    prefs = UserPrefs(day_start=time(8, 0), day_end=time(20, 0), default_session_minutes=50, max_sessions_per_day=3)
    base = datetime(2024, 1, 1, 8, 0)
    sessions = planner_engine.schedule(tasks, [], [], prefs, start=base)
    first = sessions[0]
    minutes = int((first["end_time"] - first["start_time"]).total_seconds() / 60)
    assert minutes == 44  # 0.3*30 + 0.7*50


def test_flag_off_no_change(tmp_path, monkeypatch):
    engine, db_path = _init_db(tmp_path)
    settings_on = _settings(db_path, True)
    monkeypatch.setattr(metrics, "load_settings", lambda: settings_on)
    metrics.record_session(1, 50, 30, "study", "math")
    settings_off = _settings(db_path, False)
    monkeypatch.setattr(planner_engine, "load_settings", lambda: settings_off)
    monkeypatch.setattr(metrics, "load_settings", lambda: settings_off)
    tasks = [{"id": 1, "title": "T", "type": "study", "course_label": "math", "estimated_duration": 60}]
    prefs = UserPrefs(day_start=time(8, 0), day_end=time(20, 0), default_session_minutes=50, max_sessions_per_day=3)
    base = datetime(2024, 1, 1, 8, 0)
    sessions = planner_engine.schedule(tasks, [], [], prefs, start=base)
    minutes = int((sessions[0]["end_time"] - sessions[0]["start_time"]).total_seconds() / 60)
    assert minutes == 50
