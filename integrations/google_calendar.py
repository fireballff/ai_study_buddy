from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from project.db import get_engine


class GoogleCalendarClient:
    """
    Stub implementation of a Google Calendar client. Stores events in the local DB.
    In real mode, this would interact with the Google Calendar API.
    """

    def __init__(self, engine):
        self.engine = engine

    def list_events(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        List events between start_time and end_time inclusive. Returns list of dicts.
        """
        with self.engine.begin() as conn:
            result = conn.execute(
                "SELECT id, source, source_id, title, start_time, end_time, type, description "
                "FROM events WHERE start_time >= :start AND end_time <= :end ORDER BY start_time",
                {"start": start_time.isoformat(), "end": end_time.isoformat()},
            )
            rows = result.fetchall()
            events = []
            for row in rows:
                events.append({
                    "id": row[0],
                    "source": row[1],
                    "source_id": row[2],
                    "title": row[3],
                    "start_time": datetime.fromisoformat(row[4]),
                    "end_time": datetime.fromisoformat(row[5]),
                    "type": row[6],
                    "description": row[7],
                })
            return events

    def create_event(self, title: str, start_time: datetime, end_time: datetime, event_type: str, description: str = "") -> Dict:
        with self.engine.begin() as conn:
            # Generate a pseudo source_id; in real mode this would be the Google event id
            source_id = f"local-{int(datetime.now().timestamp() * 1000)}"
            conn.execute(
                "INSERT INTO events (source, source_id, title, start_time, end_time, type, description) "
                "VALUES (:source, :source_id, :title, :start_time, :end_time, :type, :description)",
                {
                    "source": "local",
                    "source_id": source_id,
                    "title": title,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "type": event_type,
                    "description": description,
                },
            )
            event_id = conn.execute("SELECT last_insert_rowid() as id").scalar_one()
            return {
                "id": event_id,
                "source": "local",
                "source_id": source_id,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "type": event_type,
                "description": description,
            }

    def update_event(self, event_id: int, **updates) -> None:
        """
        Update an existing event with provided fields.
        """
        allowed = {"title", "start_time", "end_time", "type", "description"}
        set_clauses = []
        params: Dict[str, Any] = {"id": event_id}
        for field, value in updates.items():
            if field not in allowed:
                continue
            set_clauses.append(f"{field} = :{field}")
            if isinstance(value, datetime):
                params[field] = value.isoformat()
            else:
                params[field] = value
        if not set_clauses:
            return
        sql = "UPDATE events SET " + ", ".join(set_clauses) + " WHERE id = :id"
        with self.engine.begin() as conn:
            conn.execute(sql, params)

    def delete_event(self, event_id: int) -> None:
        with self.engine.begin() as conn:
            conn.execute("DELETE FROM events WHERE id = :id", {"id": event_id})