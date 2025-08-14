from __future__ import annotations
"""SQLite helpers for the local cache."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_engine(sqlite_path: str) -> Engine:
    """Return a SQLAlchemy engine pointing at the SQLite database."""
    return create_engine(f"sqlite:///{sqlite_path}", echo=False, future=True)


def ensure_db(engine: Engine) -> None:
    """Create tables if they do not exist."""
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        # meta table
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS app_meta ("
            " key TEXT PRIMARY KEY,"
            " value TEXT NOT NULL"
            ")"
        ))
        conn.execute(text(
            "INSERT OR IGNORE INTO app_meta(key, value) VALUES('schema', 'v2')"
        ))
        # tasks
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_user_id TEXT,
                source TEXT NOT NULL DEFAULT 'app',
                source_id TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                estimated_duration INTEGER NOT NULL DEFAULT 0,
                due_date TEXT,
                state TEXT NOT NULL DEFAULT 'pending',
                start_time TEXT,
                end_time TEXT,
                course_label TEXT,
                priority INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT,
                version TEXT NOT NULL DEFAULT '',
                dirty INTEGER NOT NULL DEFAULT 0
            )
            """
        ))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS tasks_src_idx ON tasks(owner_user_id, source, source_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS tasks_state_due_idx ON tasks(owner_user_id, state, due_date)"
        ))
        # events
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_user_id TEXT,
                source TEXT NOT NULL DEFAULT 'google',
                source_id TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                etag TEXT,
                calendar_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT,
                version TEXT NOT NULL DEFAULT '',
                dirty INTEGER NOT NULL DEFAULT 0
            )
            """
        ))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS events_src_idx ON events(owner_user_id, source, source_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS events_time_idx ON events(owner_user_id, start_time, end_time)"
        ))
        # planner preferences
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS planner_prefs (
                owner_user_id TEXT PRIMARY KEY,
                focus_block_minutes INTEGER DEFAULT 50,
                break_minutes INTEGER DEFAULT 10,
                adhd_mode_enabled INTEGER DEFAULT 0,
                dirty INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
        # blocks
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_user_id TEXT,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                dirty INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS blocks_time_idx ON blocks(owner_user_id, start_time, end_time)"
        ))
        # sync state
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                owner_user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                cursor TEXT,
                last_full_sync TEXT,
                PRIMARY KEY (owner_user_id, provider)
            )
            """
        ))
        # pending ops
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS pending_ops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                op_type TEXT NOT NULL,
                row_local_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
