from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text

from project.db_merge import merge_event, get_cursor, set_cursor


def _to_dt(val: Optional[str | datetime]) -> Optional[datetime]:
    """Accept ISO string or datetime; return datetime or None."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    # assume ISO-8601 string
    return datetime.fromisoformat(val)


class GoogleCalendarClient:
    """
    Local DB-backed calendar client (sample mode).
    - list_events(start, end): returns events in the window
    - add_event / upsert_event / delete_event: helpers for future two-way sync

    Events table expected columns:
      id INTEGER PK,
      source TEXT,
      source_id TEXT,
      title TEXT,
      start_time TEXT (ISO),
      end_time TEXT (ISO),
      type TEXT,
      description TEXT
    """

    def __init__(self, engine):
        self.engine = engine

    # ---------- Calendar helpers ----------

    def ensure_study_calendar(self) -> str:
        """Return identifier for the app's study calendar.

        In sample mode this is a no-op that returns a stub identifier.  The
        method exists so callers can ensure a dedicated calendar is present in
        live mode where real Google API keys are supplied.
        """
        # Sample mode: simply return a fixed id; live mode would check the API.
        return "study-tasks"

    def upsert_app_event(
        self,
        *,
        source_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        app_tag: str = "ai-study-buddy",
    ) -> int:
        """Idempotently upsert an app-owned event.

        Events are keyed by (source='app', source_id).  If an event already
        exists its timing/title are updated; otherwise a new row is inserted.
        """
        with self.engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT id FROM events WHERE source = :source AND source_id = :sid"
                ),
                {"source": "app", "sid": source_id},
            ).fetchone()
            event_id: Optional[int] = row[0] if row else None

        payload = {
            "source": "app",
            "source_id": source_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "type": "study_session",
            "description": description or "",
            "app_owned": 1,
            "app_tag": app_tag,
        }
        return self.upsert_event(event_id, payload)

    # ---------- Reads ----------

    def list_events(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Return events in [start_time, end_time], normalized to datetime objects.
        """
        with self.engine.begin() as conn:
            rows = conn.execute(
                text(
                    "SELECT id, source, source_id, title, start_time, end_time, type, description "
                    "FROM events "
                    "WHERE start_time < :end AND end_time > :start "
                    "ORDER BY start_time"
                ),
                {"start": start_time.isoformat(), "end": end_time.isoformat()},
            ).fetchall()

        events: List[Dict[str, Any]] = []
        for row in rows:
            (eid, source, source_id, title, start_iso, end_iso, etype, desc) = row
            events.append(
                {
                    "id": eid,
                    "source": source,
                    "source_id": source_id,
                    "title": title,
                    "start_time": _to_dt(start_iso),
                    "end_time": _to_dt(end_iso),
                    "type": etype,
                    "description": desc,
                }
            )
        return events

    def fetch_since(self, provider: str = "google", since_cursor: Optional[str] = None) -> str:
        """Merge events from staging_events updated after the cursor.

        If ``since_cursor`` is not provided, the last stored cursor for the
        provider is used. Merged events are written to the ``events`` table via
        :func:`merge_event`. The sync cursor is then advanced to ``datetime.utcnow()``.
        """
        with self.engine.begin() as conn:
            cursor = since_cursor or get_cursor(conn, provider)
            if cursor:
                rows = conn.execute(
                    text(
                        "SELECT source, source_id, title, start_time, end_time, type, description, updated_at "
                        "FROM staging_events WHERE updated_at > :cursor ORDER BY updated_at"
                    ),
                    {"cursor": cursor},
                ).fetchall()
            else:
                rows = conn.execute(
                    text(
                        "SELECT source, source_id, title, start_time, end_time, type, description, updated_at "
                        "FROM staging_events ORDER BY updated_at"
                    )
                ).fetchall()
            for row in rows:
                (source, source_id, title, start_iso, end_iso, etype, desc, _upd) = row
                merge_event(
                    conn,
                    {
                        "source": source,
                        "source_id": source_id,
                        "title": title,
                        "start_time": start_iso,
                        "end_time": end_iso,
                        "type": etype,
                        "description": desc,
                    },
                )
            new_cursor = datetime.utcnow().isoformat()
            set_cursor(conn, provider, new_cursor)
        return new_cursor

    # ---------- Writes (for future two-way sync) ----------

    def add_event(
        self,
        *,
        title: str,
        start_time: datetime,
        end_time: datetime,
        etype: Optional[str] = None,
        description: Optional[str] = None,
        source: str = "local",
        source_id: Optional[str] = None,
    ) -> int:
        """
        Insert a new event into the local DB and return its new id.
        """
        payload = {
            "source": source,
            "source_id": source_id,
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "type": etype,
            "description": description,
        }
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO events (source, source_id, title, start_time, end_time, type, description) "
                    "VALUES (:source, :source_id, :title, :start_time, :end_time, :type, :description)"
                ),
                payload,
            )
            new_id = conn.execute(text("SELECT last_insert_rowid() AS id")).scalar_one()
        return int(new_id)

    def upsert_event(self, event_id: Optional[int], updates: Dict[str, Any]) -> int:
        """
        Create or update an event. If event_id is None, create. Otherwise update.
        updates keys should align with columns: title, start_time (dt/iso), end_time (dt/iso), type, description, source, source_id
        Returns the event id.
        """
        norm: Dict[str, Any] = {}
        for k, v in updates.items():
            if k in ("start_time", "end_time") and isinstance(v, datetime):
                norm[k] = v.isoformat()
            else:
                norm[k] = v

        with self.engine.begin() as conn:
            if event_id is None:
                # Insert path
                cols = ", ".join(norm.keys())
                binds = ", ".join(f":{k}" for k in norm.keys())
                conn.execute(text(f"INSERT INTO events ({cols}) VALUES ({binds})"), norm)
                event_id = conn.execute(text("SELECT last_insert_rowid() AS id")).scalar_one()
                if event_id is None:
                    raise ValueError("Failed to retrieve event id after insert.")
                return int(event_id)
            else:
                # Update path
                set_clause = ", ".join(f"{k} = :{k}" for k in norm.keys())
                norm["id"] = event_id
                conn.execute(text(f"UPDATE events SET {set_clause} WHERE id = :id"), norm)
                return int(event_id)

    def delete_event(self, event_id: int) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM events WHERE id = :id"), {"id": event_id})
