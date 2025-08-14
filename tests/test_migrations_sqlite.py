from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def run_migration_0007(db_path: Path) -> Config:
    cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    # pretend previous migrations already ran
    command.stamp(cfg, "0006_calendar_indexes")
    command.upgrade(cfg, "head")
    return cfg


def test_sqlite_migrations_handle_partial_state(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state TEXT,
                    due_date TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_user_id TEXT,
                    source TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT ''
                )
                """
            )
        )
        # stray temp table from failed prior run
        conn.execute(text("CREATE TABLE IF NOT EXISTS _alembic_tmp_events(id INTEGER)"))

    cfg = run_migration_0007(db_path)
    # running again should be a no-op
    command.upgrade(cfg, "head")

    insp = inspect(engine)
    assert "_alembic_tmp_events" not in insp.get_table_names()
    assert "staging_events" in insp.get_table_names()

    st_cols = {c["name"] for c in insp.get_columns("staging_events")}
    assert {"etag", "sync_timestamp"}.issubset(st_cols)

    ev_cols = {c["name"] for c in insp.get_columns("events")}
    for col in ["etag", "updated_at", "last_synced_at", "app_owned", "app_tag"]:
        assert col in ev_cols
