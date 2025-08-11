from __future__ import annotations
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Tuple
import os

from integrations.google_calendar import GoogleCalendarClient
from agents.nudges import generate_nudges


ENABLE_LIVE_RESCHEDULE = os.getenv("ENABLE_LIVE_RESCHEDULE", "false").lower() == "true"
ENABLE_MICRO_COACHING = os.getenv("ENABLE_MICRO_COACHING", "false").lower() == "true"


def schedule_tasks(
    tasks: List[Dict],
    events: List[Dict],
    *,
    work_start: time = time(8, 0),
    work_end: time = time(20, 0),
    calendar_client: GoogleCalendarClient | None = None,
) -> List[Dict]:
    """
    Simple scheduling algorithm: places tasks in available time slots between events.

    - Tasks are sorted by due_date then title.
    - Events must have 'start_time' and 'end_time' as datetime objects.
    - Each task dict must contain 'estimated_duration' in minutes.
    - Returns list of tasks with 'start_time' and 'end_time' assigned.
    """
    # Sort tasks by due_date (None last) and then title
    def task_key(t: Dict):
        due = t.get('due_date')
        return (due if due is not None else datetime.max, t['title'])
    tasks_sorted = sorted(tasks, key=task_key)

    # Build busy intervals from events and tasks that already have start_time
    busy: List[Tuple[datetime, datetime]] = []
    for ev in events:
        busy.append((ev['start_time'], ev['end_time']))
    # Keep tasks to schedule; tasks may have pre-assigned times (future reschedules)
    for t in tasks_sorted:
        if t.get('start_time') and t.get('end_time'):
            busy.append((t['start_time'], t['end_time']))
    busy.sort()

    scheduled: List[Dict] = []
    per_task_index: Dict[int, int] = {}
    if ENABLE_LIVE_RESCHEDULE and calendar_client:
        calendar_client.ensure_study_calendar()
    for task in tasks_sorted:
        if task.get('start_time') and task.get('end_time'):
            scheduled.append(task)
            continue
        duration_minutes = task.get('estimated_duration', 60)
        scheduled_time = _find_slot(duration_minutes, busy, work_start, work_end)
        if scheduled_time is None:
            # No available slot today: place task after the last busy block,
            # but roll over to next work day if it exceeds today's work window.
            last_end = busy[-1][1] if busy else datetime.combine(date.today(), work_start)
            tentative_start = (last_end + timedelta(minutes=5)).replace(second=0, microsecond=0)
            day_end_dt = datetime.combine(tentative_start.date(), work_end)
            tentative_end = tentative_start + timedelta(minutes=duration_minutes)
            if tentative_start >= day_end_dt or tentative_end > day_end_dt:
                next_day = tentative_start.date() + timedelta(days=1)
                start = datetime.combine(next_day, work_start)
                end = start + timedelta(minutes=duration_minutes)
            else:
                start, end = tentative_start, tentative_end
        else:
            start, end = scheduled_time
        task_copy = task.copy()
        task_copy['start_time'] = start
        task_copy['end_time'] = end
        scheduled.append(task_copy)
        busy.append((start, end))
        busy.sort()
        if ENABLE_LIVE_RESCHEDULE and calendar_client:
            idx = per_task_index.get(task['id'], 0)
            per_task_index[task['id']] = idx + 1
            calendar_client.upsert_app_event(
                source_id=f"task:{task['id']}:{idx}",
                title=task['title'],
                start_time=start,
                end_time=end,
            )

    if ENABLE_MICRO_COACHING:
        nudges = generate_nudges(scheduled, tasks)
        return scheduled, nudges

    return scheduled


def _find_slot(duration: int, busy: List[Tuple[datetime, datetime]], work_start: time, work_end: time) -> Tuple[datetime, datetime] | None:
    """
    Find the next available time slot of `duration` minutes given a list of busy intervals.
    """
    # convert busy intervals to same-day intervals and search within work hours of today
    today = date.today()
    day_start = datetime.combine(today, work_start)
    day_end = datetime.combine(today, work_end)
    # Start scanning from day_start
    pointer = day_start
    for bstart, bend in busy:
        if bend <= pointer:
            continue
        # If the next busy interval is after pointer, check gap
        if bstart > pointer:
            gap = (bstart - pointer).total_seconds() / 60
            if gap >= duration:
                return pointer, pointer + timedelta(minutes=duration)
            pointer = bend
            continue
        else:
            # overlapping or contiguous busy
            if bend > pointer:
                pointer = bend
    # Check remaining time after last busy interval
    if (day_end - pointer).total_seconds() / 60 >= duration:
        return pointer, pointer + timedelta(minutes=duration)
    return None
