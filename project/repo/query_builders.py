"""SQL query builders shared across repositories."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Tuple, Dict


def build_tasks_query(
    filter_mode: str,
    search: str,
    *,
    include_sync_columns: bool = False,
) -> Tuple[str, Dict[str, str]]:
    """Construct SQL and params for tasks filtering.

    If ``include_sync_columns`` is True, additional sync metadata columns are
    included in the SELECT list. Tests that create their own schema can rely on
    the default which matches the legacy column set.
    """
    where_clauses = []
    params: Dict[str, str] = {}

    if filter_mode == "Today":
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        params["today"] = today.isoformat()
        params["tomorrow"] = tomorrow.isoformat()
        where_clauses.append(
            "(state = 'pending' OR (start_time >= :today AND start_time < :tomorrow))"
        )
        order_clause = "ORDER BY COALESCE(start_time, due_date)"
    elif filter_mode == "Upcoming":
        where_clauses.append("due_date IS NOT NULL")
        order_clause = "ORDER BY due_date"
    elif filter_mode == "By Course":
        order_clause = (
            "ORDER BY COALESCE(course_label, ''), COALESCE(due_date, '9999-12-31')"
        )
    elif filter_mode == "By Priority":
        order_clause = (
            "ORDER BY COALESCE(priority, 3), COALESCE(due_date, '9999-12-31')"
        )
    else:  # All
        order_clause = "ORDER BY created_at"

    if search:
        params["q"] = f"%{search.lower()}%"
        where_clauses.append(
            "(LOWER(title) LIKE :q OR LOWER(type) LIKE :q OR LOWER(COALESCE(course_label,'')) LIKE :q)"
        )

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    cols = [
        "id",
        "title",
        "type",
        "estimated_duration",
        "due_date",
        "state",
        "start_time",
        "end_time",
        "course_label",
        "priority",
    ]
    if include_sync_columns:
        cols.extend(
            ["owner_user_id", "source", "source_id", "updated_at", "version", "dirty"]
        )
    cols_sql = ", ".join(cols)
    sql = f"SELECT {cols_sql} FROM tasks {where_sql} {order_clause}"
    return sql, params
