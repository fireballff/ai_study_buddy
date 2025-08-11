from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from project.db import get_engine
from project.db_merge import merge_event
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


def test_conflict_policy_creates_copy(tmp_path, caplog):
    engine = setup_engine(tmp_path)
    client = GoogleCalendarClient(engine)
    base_start = "2024-01-01T09:00:00"
    base_end = "2024-01-01T10:00:00"
    now = datetime.utcnow()
    earlier = (now - timedelta(days=1)).isoformat()
    later = (now + timedelta(days=1)).isoformat()
    # initial remote insert with older timestamp
    with engine.begin() as conn:
        merge_event(
            conn,
            {
                "source": "google",
                "source_id": "ev1",
                "title": "Original",
                "start_time": base_start,
                "end_time": base_end,
                "type": "meeting",
                "description": "",
                "updated_at": earlier,
                "etag": "v1",
            },
        )
    # local edit after sync
    with engine.begin() as conn:
        eid = conn.execute(text("SELECT id FROM events WHERE source='google'"))
        event_id = int(eid.scalar_one())
    client.upsert_event(event_id, {"title": "Local edit"})
    # remote change after local edit triggers conflict
    with engine.begin() as conn:
        merge_event(
            conn,
            {
                "source": "google",
                "source_id": "ev1",
                "title": "Remote edit",
                "start_time": base_start,
                "end_time": base_end,
                "type": "meeting",
                "description": "",
                "updated_at": later,
                "etag": "v2",
            },
        )
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT title, source, source_id, etag, last_synced_at FROM events ORDER BY id")
        ).fetchall()
    assert len(rows) == 2
    titles = {r[0] for r in rows}
    assert "Remote edit" in titles
    assert "Local edit (conflict)" in titles
    remote_row = next(r for r in rows if r[0] == "Remote edit")
    assert remote_row[3] == "v2"
    assert remote_row[4] is not None
    # re-merge should be idempotent
    with engine.begin() as conn:
        merge_event(
            conn,
            {
                "source": "google",
                "source_id": "ev1",
                "title": "Remote edit",
                "start_time": base_start,
                "end_time": base_end,
                "type": "meeting",
                "description": "",
                "updated_at": "2024-01-02T08:00:00",
                "etag": "v2",
            },
        )
    with engine.begin() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM events")).scalar_one()
    assert count == 2
