from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from project.prefs import UserPrefs
from project import metrics
from project.settings import load_settings


def _to_datetime(value: Optional[datetime | date | str], end_of_day: time) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, end_of_day)
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _subtract_intervals(base: List[Tuple[datetime, datetime]], busy: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    """Subtract busy intervals from base intervals."""
    result: List[Tuple[datetime, datetime]] = []
    busy_sorted = sorted(busy)
    for start, end in base:
        cur = start
        for bstart, bend in busy_sorted:
            if bend <= cur or bstart >= end:
                continue
            if bstart > cur:
                result.append((cur, min(bstart, end)))
            cur = max(cur, bend)
            if cur >= end:
                break
        if cur < end:
            result.append((cur, end))
    return result


def schedule(tasks: List[Dict], events: List[Dict], blocks: List[Dict], prefs: UserPrefs, *, start: Optional[datetime] = None, horizon_days: int = 7) -> List[Dict]:
    """
    Schedule tasks into study sessions respecting events, blocks, deadlines and preferences.
    Returns list of sessions with keys: task_id, title, start_time, end_time, rationale.
    """
    base_dt = (start or datetime.now()).replace(second=0, microsecond=0)
    today = base_dt.date()
    horizon_end = datetime.combine(today, time.min) + timedelta(days=horizon_days)

    # Build busy intervals from events and busy blocks
    busy: List[Tuple[datetime, datetime]] = []
    for ev in events:
        busy.append((ev['start_time'], ev['end_time']))
    for b in blocks:
        if b.get('kind') == 'busy':
            busy.append((b['start_time'], b['end_time']))
    busy.sort()

    # Build study windows (intersection with prefs day_start/day_end)
    study_blocks = [b for b in blocks if b.get('kind') == 'study_window']
    daily_windows: List[Tuple[datetime, datetime]] = []
    for offset in range(horizon_days):
        day = today + timedelta(days=offset)
        base_start = datetime.combine(day, prefs.day_start)
        base_end = datetime.combine(day, prefs.day_end)
        if base_start >= horizon_end:
            break
        relevant: List[Tuple[datetime, datetime]] = []
        for sw in study_blocks:
            sw_start, sw_end = sw['start_time'], sw['end_time']
            if sw_end <= base_start or sw_start >= base_end:
                continue
            start_i = max(base_start, sw_start)
            end_i = min(base_end, sw_end)
            if start_i < end_i:
                relevant.append((start_i, end_i))
        if relevant:
            daily_windows.extend(relevant)
        else:
            daily_windows.append((base_start, base_end))

    free_slots = _subtract_intervals(daily_windows, busy)
    free_slots.sort()

    # Sort tasks
    def task_key(t: Dict):
        due_dt = _to_datetime(t.get('due_date'), prefs.day_end) or horizon_end
        priority = t.get('priority') if t.get('priority') is not None else 999
        return (due_dt, priority, -t.get('estimated_duration', 0))

    tasks_sorted = sorted([t for t in tasks if t.get('state') in (None, 'pending')], key=task_key)

    sessions: List[Dict] = []
    sessions_per_day: defaultdict[date, int] = defaultdict(int)
    settings = load_settings()
    use_learning = getattr(settings, "enable_learning_loop", False)

    # Scheduler loop
    for task in tasks_sorted:
        remaining = task.get('estimated_duration', 0)
        if remaining <= 0:
            continue
        due_dt = _to_datetime(task.get('due_date'), prefs.day_end) or horizon_end

        i = 0
        while remaining > 0 and i < len(free_slots):
            slot_start, slot_end = free_slots[i]
            day = slot_start.date()
            if slot_start >= due_dt:
                break
            if sessions_per_day[day] >= prefs.max_sessions_per_day:
                i += 1
                continue
            allowed_end = min(slot_end, due_dt)
            if allowed_end <= slot_start:
                i += 1
                continue
            available = (allowed_end - slot_start).total_seconds() / 60
            if available <= 0:
                i += 1
                continue
            session_minutes = prefs.default_session_minutes
            if use_learning:
                session_minutes = metrics.get_estimate(
                    task.get("type"), task.get("course_label"), session_minutes
                )
            chunk = min(session_minutes, remaining, available)
            session_start = slot_start
            session_end = session_start + timedelta(minutes=chunk)
            sessions.append({
                'task_id': task['id'],
                'title': task['title'],
                'type': task.get('type'),
                'start_time': session_start,
                'end_time': session_end,
                'rationale': f"due {due_dt.date()} priority {task.get('priority')}",
            })
            remaining -= chunk
            sessions_per_day[day] += 1
            # Update slot
            new_start = session_end
            if new_start < slot_end and new_start < allowed_end and sessions_per_day[day] < prefs.max_sessions_per_day:
                free_slots[i] = (new_start, slot_end)
            else:
                free_slots.pop(i)
                continue  # don't increment i; next slot now at same index
            if remaining <= 0:
                break
        # end while slots
    return sessions
