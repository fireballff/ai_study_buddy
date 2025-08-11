from __future__ import annotations
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from project.db import get_engine
from project.db_merge import merge_event, get_cursor, set_cursor
from integrations.google_calendar import GoogleCalendarClient


def run_migrations(db_path: Path) -> None:
    cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parent.parent / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(cfg, "head")


def setup_engine(tmp_path):
    db_path = tmp_path / "test.db"
    run_migrations(db_path)
    return get_engine(str(db_path))


def test_merge_event_idempotent(tmp_path):
    engine = setup_engine(tmp_path)
    ev = {
        "source": "google",
        "source_id": "ev1",
        "title": "Meeting",
        "start_time": "2024-01-01T09:00:00",
        "end_time": "2024-01-01T10:00:00",
        "type": "meeting",
        "description": "",
    }
    with engine.begin() as conn:
        id1 = merge_event(conn, ev)
        id2 = merge_event(conn, ev)
        assert id1 == id2
        count = conn.execute(text("SELECT COUNT(*) FROM events")).scalar_one()
        assert count == 1


def test_cursor_roundtrip(tmp_path):
    engine = setup_engine(tmp_path)
    with engine.begin() as conn:
        assert get_cursor(conn, "google") is None
        set_cursor(conn, "google", "2024-01-01T00:00:00")
        assert get_cursor(conn, "google") == "2024-01-01T00:00:00"
        set_cursor(conn, "google", "2024-01-02T00:00:00")
        assert get_cursor(conn, "google") == "2024-01-02T00:00:00"


def test_client_list_and_fetch_since(tmp_path):
    engine = setup_engine(tmp_path)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO staging_events (source, source_id, title, start_time, end_time, type, description, updated_at) "
                "VALUES (:source, :source_id, :title, :start_time, :end_time, :type, :description, :updated_at)"
            ),
            [
                {
                    "source": "google",
                    "source_id": "1",
                    "title": "Event1",
                    "start_time": "2024-01-01T09:00:00",
                    "end_time": "2024-01-01T10:00:00",
                    "type": "meeting",
                    "description": "",
                    "updated_at": "2024-01-01T08:00:00",
                },
                {
                    "source": "google",
                    "source_id": "2",
                    "title": "Event2",
                    "start_time": "2024-01-02T09:00:00",
                    "end_time": "2024-01-02T10:00:00",
                    "type": "meeting",
                    "description": "",
                    "updated_at": "2024-01-02T08:00:00",
                },
            ],
        )
    client = GoogleCalendarClient(engine)
    cursor = client.fetch_since("google")
    with engine.begin() as conn:
        stored = get_cursor(conn, "google")
    assert stored == cursor
    start = datetime.fromisoformat("2024-01-01T00:00:00")
    end = datetime.fromisoformat("2024-01-03T00:00:00")
    events = client.list_events(start, end)
    titles = {e["title"] for e in events}
    assert {"Event1", "Event2"} <= titles
    cursor2 = client.fetch_since("google", cursor)
    assert cursor2 > cursor
    events2 = client.list_events(start, end)
    assert len(events2) == len(events)
