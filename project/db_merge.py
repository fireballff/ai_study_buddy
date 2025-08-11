from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
from sqlalchemy import text


def _norm_event(event: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for key in [
        "source",
        "source_id",
        "title",
        "start_time",
        "end_time",
        "type",
        "description",
        "etag",
        "updated_at",
    ]:
        if key not in event:
            continue
        val = event.get(key)
        if key in ("start_time", "end_time") and isinstance(val, datetime):
            payload[key] = val.isoformat()
        elif key == "updated_at" and isinstance(val, datetime):
            payload[key] = val.isoformat()
        else:
            payload[key] = val
    return payload


def merge_event(conn, event: Dict[str, Any], logger: Optional[structlog.BoundLogger] = None) -> int:
    """Insert or update an event record and return its id.

    Conflict policy:
        - If the local row was edited after the last sync and the remote version
          changed, keep the remote update but create a local "conflict" copy of
          the unsynced changes.
        - Otherwise, whichever side has the newer ``updated_at`` wins.
    """
    logger = logger or structlog.get_logger(__name__)
    payload = _norm_event(event)
    lookup = {"source": payload["source"], "source_id": payload["source_id"]}
    row = conn.execute(
        text(
            "SELECT id, title, start_time, end_time, type, description, etag, updated_at, last_synced_at "
            "FROM events WHERE source = :source AND source_id = :source_id"
        ),
        lookup,
    ).fetchone()
    now = datetime.utcnow().isoformat()
    remote_updated = payload.get("updated_at", now)
    remote_etag = payload.get("etag")
    if row:
        event_id = int(row.id if hasattr(row, "id") else row[0])
        local_updated = row.updated_at if hasattr(row, "updated_at") else row[7]
        last_synced = row.last_synced_at if hasattr(row, "last_synced_at") else row[8]
        local_edited = bool(last_synced and local_updated and local_updated > last_synced)
        remote_changed = bool(last_synced is None or remote_updated > last_synced)
        if local_edited and remote_changed:
            conflict_payload = {
                "source": "local",
                "source_id": f"conflict-{event_id}",
                "title": f"{row.title} (conflict)",
                "start_time": row.start_time,
                "end_time": row.end_time,
                "type": row.type,
                "description": row.description,
                "updated_at": local_updated,
            }
            conn.execute(
                text(
                    "INSERT INTO events (source, source_id, title, start_time, end_time, type, description, updated_at) "
                    "VALUES (:source, :source_id, :title, :start_time, :end_time, :type, :description, :updated_at)"
                ),
                conflict_payload,
            )
            logger.warning("sync_conflict", source_id=lookup["source_id"])
        keep_remote = not local_edited or remote_updated >= local_updated
        if keep_remote:
            conn.execute(
                text(
                    "UPDATE events SET title=:title, start_time=:start_time, end_time=:end_time, "
                    "type=:type, description=:description, etag=:etag, updated_at=:updated_at, last_synced_at=:last_synced_at "
                    "WHERE id=:id"
                ),
                {
                    **payload,
                    "etag": remote_etag,
                    "updated_at": remote_updated,
                    "last_synced_at": now,
                    "id": event_id,
                },
            )
        else:
            conn.execute(
                text(
                    "UPDATE events SET last_synced_at=:last_synced_at WHERE id=:id"
                ),
                {"last_synced_at": now, "id": event_id},
            )
        return event_id
    # No existing row: insert
    insert_payload = {
        **payload,
        "etag": remote_etag,
        "updated_at": remote_updated,
        "last_synced_at": now,
    }
    cols = ", ".join(insert_payload.keys())
    binds = ", ".join(f":{k}" for k in insert_payload.keys())
    conn.execute(text(f"INSERT INTO events ({cols}) VALUES ({binds})"), insert_payload)
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
