from __future__ import annotations
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from datetime import datetime


def get_engine(sqlite_path: str) -> Engine:
    """
    Return a SQLAlchemy engine pointing at the SQLite database.
    """
    return create_engine(f"sqlite:///{sqlite_path}", echo=False, future=True)


def ensure_db(engine: Engine) -> None:
    """
    Ensure the base tables exist. This function uses raw SQL for simplicity.
    If the tables already exist, calls have no effect.
    """
    with engine.begin() as conn:
        # meta table for schema version
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS app_meta ("
            " key TEXT PRIMARY KEY,"
            " value TEXT NOT NULL"
            ")"
        ))
        conn.execute(text(
            "INSERT OR IGNORE INTO app_meta(key, value) VALUES('schema', 'v1')"
        ))

        # events table (for imported calendar events)
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS events ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " source TEXT NOT NULL,"
            " source_id TEXT NOT NULL,"
            " title TEXT NOT NULL,"
            " start_time TEXT NOT NULL,"
            " end_time TEXT NOT NULL,"
            " type TEXT NOT NULL,"
            " description TEXT DEFAULT ''"
            ")"
        ))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS events_source_idx ON events (source, source_id)"
        ))

        # tasks table (user tasks with optional planned times)
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS tasks ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " title TEXT NOT NULL,"
            " type TEXT NOT NULL,"
            " estimated_duration INTEGER NOT NULL,"
            " due_date TEXT,"
            " course_label TEXT,"
            " created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            " updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,"
            " start_time TEXT,"
            " end_time TEXT,"
            " state TEXT NOT NULL DEFAULT 'pending'"
            ")"
        ))