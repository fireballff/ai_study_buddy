from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text


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
                    "WHERE start_time >= :start AND end_time <= :end "
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
