from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List
from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class CalendarItem:
    """Unified representation of a calendar item."""
    id: int
    title: str
    start: datetime
    end: datetime
    type: str
    source: str  # "task" or event source
    table: str   # underlying table name


class CalendarModel:
    """Read-only access layer for calendar items grouped by day."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.tz = datetime.now().astimezone().tzinfo

    def _normalize(self, dt_str: str) -> datetime:
        """Convert an ISO string to local timezone."""
        if not dt_str:
            raise ValueError("datetime string required")
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.tz)
        return dt.astimezone(self.tz)

    def fetch_range(self, start: date, end: date) -> Dict[date, List[CalendarItem]]:
        """Return calendar items grouped by day between start and end (inclusive)."""
        # compute range boundaries
        start_dt = datetime.combine(start, datetime.min.time()).astimezone(self.tz)
        end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time()).astimezone(self.tz)
        items: Dict[date, List[CalendarItem]] = {}
        with self.engine.begin() as conn:
            # tasks
            task_rows = conn.execute(
                text(
                    """
                    SELECT id, title, start_time, end_time, type
                    FROM tasks
                    WHERE start_time IS NOT NULL AND end_time IS NOT NULL
                      AND start_time < :end AND end_time >= :start
                    """
                ),
                {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
            )
            for row in task_rows:
                start_local = self._normalize(row.start_time)
                end_local = self._normalize(row.end_time)
                day = start_local.date()
                item = CalendarItem(
                    id=row.id,
                    title=row.title,
                    start=start_local,
                    end=end_local,
                    type=row.type,
                    source="task",
                    table="tasks",
                )
                items.setdefault(day, []).append(item)

            # events
            event_rows = conn.execute(
                text(
                    """
                    SELECT id, source, source_id, title, start_time, end_time, type
                    FROM events
                    WHERE start_time < :end AND end_time >= :start
                    """
                ),
                {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
            )
            for row in event_rows:
                start_local = self._normalize(row.start_time)
                end_local = self._normalize(row.end_time)
                day = start_local.date()
                item = CalendarItem(
                    id=row.id,
                    title=row.title,
                    start=start_local,
                    end=end_local,
                    type=row.type,
                    source=row.source,
                    table="events",
                )
                items.setdefault(day, []).append(item)
        return items

    # helper methods for UI actions
    def delete_item(self, item: CalendarItem) -> None:
        """Remove an item from the underlying table."""
        table = item.table
        with self.engine.begin() as conn:
            conn.execute(
                text(f"DELETE FROM {table} WHERE id = :id"), {"id": item.id}
            )

    def update_item_time(
        self, item: CalendarItem, new_start: datetime, new_end: datetime
    ) -> None:
        """Persist a time change for a calendar item.

        Only application-owned events and tasks can be updated. External
        calendar events are ignored to avoid mutating data the app does not
        control.
        """

        # guard against modifying third-party events
        if item.table == "events" and item.source != "app":
            return

        with self.engine.begin() as conn:
            conn.execute(
                text(
                    f"""
                    UPDATE {item.table}
                    SET start_time = :start, end_time = :end
                    WHERE id = :id
                    """
                ),
                {
                    "start": new_start.astimezone(self.tz).isoformat(),
                    "end": new_end.astimezone(self.tz).isoformat(),
                    "id": item.id,
                },
            )
