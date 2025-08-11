from __future__ import annotations
from datetime import datetime, date, timezone, timedelta
from sqlalchemy import text

from project.db import get_engine, ensure_db
from ui.calendar.calendar_model import CalendarModel


def test_calendar_model_groups_and_normalizes(tmp_path):
    db_path = tmp_path / "cal.db"
    engine = get_engine(str(db_path))
    ensure_db(engine)
    utc = timezone.utc
    event_start = datetime(2024, 1, 1, 15, 0, tzinfo=utc)
    event_end = event_start + timedelta(hours=1)
    task_start = datetime(2024, 1, 2, 9, 0)
    task_end = task_start + timedelta(hours=2)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO events (source, source_id, title, start_time, end_time, type, description)
                VALUES ('local','e1','Meeting',:s,:e,'meeting','')
                """
            ),
            {"s": event_start.isoformat(), "e": event_end.isoformat()},
        )
        conn.execute(
            text(
                """
                INSERT INTO tasks (title, type, estimated_duration, start_time, end_time)
                VALUES ('Write essay','homework',120,:s,:e)
                """
            ),
            {"s": task_start.isoformat(), "e": task_end.isoformat()},
        )
    model = CalendarModel(engine)
    items = model.fetch_range(date(2024, 1, 1), date(2024, 1, 3))
    local_day_event = event_start.astimezone().date()
    assert local_day_event in items
    assert task_start.date() in items
    # normalization to local timezone
    ev = items[local_day_event][0]
    assert ev.start.tzinfo == datetime.now().astimezone().tzinfo
    # grouping counts
    assert len(items[local_day_event]) == 1
    assert len(items[task_start.date()]) == 1
    # range filter
    narrow = model.fetch_range(date(2024, 1, 1), date(2024, 1, 1))
    assert local_day_event in narrow
    assert task_start.date() not in narrow
