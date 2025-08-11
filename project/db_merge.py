from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text


def _norm_event(event: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for key in ["source", "source_id", "title", "start_time", "end_time", "type", "description"]:
        val = event.get(key)
        if key in ("start_time", "end_time") and isinstance(val, datetime):
            payload[key] = val.isoformat()
        else:
            payload[key] = val
    return payload


def merge_event(conn, event: Dict[str, Any]) -> int:
    """Insert or update an event record and return its id.

    Deduplicate by (source, source_id) if present. As a fallback, deduplicate
    by (title, start_time).
    """
    payload = _norm_event(event)
    lookup = {"source": payload["source"], "source_id": payload["source_id"]}
    row = conn.execute(
        text("SELECT id FROM events WHERE source = :source AND source_id = :source_id"),
        lookup,
    ).fetchone()
    if row:
        event_id = int(row.id if hasattr(row, "id") else row[0])
        conn.execute(
            text(
                "UPDATE events SET title=:title, start_time=:start_time, end_time=:end_time, "
                "type=:type, description=:description WHERE id=:id"
            ),
            {**payload, "id": event_id},
        )
        return event_id
    # Fallback dedupe by title + start_time
    row = conn.execute(
        text("SELECT id FROM events WHERE title = :title AND start_time = :start_time"),
        {"title": payload["title"], "start_time": payload["start_time"]},
    ).fetchone()
    if row:
        event_id = int(row.id if hasattr(row, "id") else row[0])
        conn.execute(
            text(
                "UPDATE events SET source=:source, source_id=:source_id, end_time=:end_time, "
                "type=:type, description=:description WHERE id=:id"
            ),
            {**payload, "id": event_id},
        )
        return event_id
    # Insert new
    conn.execute(
        text(
            "INSERT INTO events (source, source_id, title, start_time, end_time, type, description) "
            "VALUES (:source, :source_id, :title, :start_time, :end_time, :type, :description)"
        ),
        payload,
    )
    event_id = conn.execute(text("SELECT last_insert_rowid() AS id")).scalar_one()
    return int(event_id)


def get_cursor(conn, provider: str) -> Optional[str]:
    row = conn.execute(
        text("SELECT cursor FROM sync_cursors WHERE provider = :provider"),
        {"provider": provider},
    ).fetchone()
    if row:
        return row.cursor if hasattr(row, "cursor") else row[0]
    return None


def set_cursor(conn, provider: str, cursor: str) -> None:
    conn.execute(
        text(
            "INSERT INTO sync_cursors(provider, cursor) VALUES(:provider, :cursor) "
            "ON CONFLICT(provider) DO UPDATE SET cursor = excluded.cursor"
        ),
        {"provider": provider, "cursor": cursor},
    )
