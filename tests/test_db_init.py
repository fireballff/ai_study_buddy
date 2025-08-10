from __future__ import annotations
from project.db import get_engine, ensure_db
from sqlalchemy import text


def test_db_created_and_seeded(tmp_path):
    db_path = tmp_path / "test.db"
    engine = get_engine(str(db_path))
    ensure_db(engine)
    with engine.begin() as conn:
        rows = list(conn.execute(text("SELECT key, value FROM app_meta")))
        assert rows, "app_meta table should contain at least one row"
        events_table = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='events'"))
        assert events_table.fetchone() is not None, "events table should be created"