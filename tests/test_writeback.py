from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from integrations.google_calendar import GoogleCalendarClient


def setup_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    app_owned INTEGER DEFAULT 0,
                    app_tag TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX events_source_idx ON events (source, source_id)"
            )
        )
    return engine


def test_upsert_app_event_local_sample_mode_idempotent():
    engine = setup_engine()
    client = GoogleCalendarClient(engine)
    now = datetime.now().replace(microsecond=0)
    later = now + timedelta(hours=1)
    sid = "task:1:0"

    # First insert
    eid = client.upsert_app_event(
        source_id=sid,
        title="Session 1",
        start_time=now,
        end_time=later,
    )
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT id, title, start_time, end_time, app_owned, app_tag FROM events WHERE source='app' AND source_id=:sid"
            ),
            {"sid": sid},
        ).mappings().first()
    assert row is not None
    assert row["id"] == eid
    assert row["app_owned"] == 1
    assert row["app_tag"] == "ai-study-buddy"

    # Second update with new times/title
    new_start = now + timedelta(days=1)
    new_end = new_start + timedelta(hours=1)
    eid2 = client.upsert_app_event(
        source_id=sid,
        title="Session 2",
        start_time=new_start,
        end_time=new_end,
    )
    assert eid2 == eid
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT id, title, start_time, end_time FROM events WHERE source='app' AND source_id=:sid"),
            {"sid": sid},
        ).mappings().all()
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == eid
    assert row["title"] == "Session 2"
    assert row["start_time"] == new_start.isoformat()
    assert row["end_time"] == new_end.isoformat()
