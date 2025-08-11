from __future__ import annotations
from datetime import datetime, time, timedelta

from agents.planner import schedule_tasks


def test_schedule_tasks_avoids_event_overlap():
    tasks = [
        {'id': 1, 'title': 'Task A', 'type': 'homework', 'estimated_duration': 60, 'due_date': None},
        {'id': 2, 'title': 'Task B', 'type': 'study', 'estimated_duration': 60, 'due_date': None},
    ]
    events = [
        {
            'id': 1,
            'source': 'local',
            'source_id': 'ev1',
            'title': 'Meeting',
            'start_time': datetime.combine(datetime.today(), time(10, 0)),
            'end_time': datetime.combine(datetime.today(), time(11, 0)),
            'type': 'meeting',
            'description': '',
        }
    ]
    scheduled = schedule_tasks(tasks, events, work_start=time(9, 0), work_end=time(12, 0))
    # ensure both tasks get scheduled
    assert len(scheduled) == 2
    # tasks should not overlap with the meeting event
    for task in scheduled:
        assert not (
            (task['start_time'] < events[0]['end_time'] and task['end_time'] > events[0]['start_time'])
        )
    # tasks should not overlap each other
    t1, t2 = scheduled
    assert t1['end_time'] <= t2['start_time'] or t2['end_time'] <= t1['start_time']


def test_schedule_tasks_rolls_over_when_start_after_work_end():
    tasks = [
        {'id': 1, 'title': 'Task A', 'type': 'homework', 'estimated_duration': 60, 'due_date': None},
        {'id': 2, 'title': 'Task B', 'type': 'study', 'estimated_duration': 45, 'due_date': None},
    ]
    scheduled = schedule_tasks(tasks, [], work_start=time(9, 0), work_end=time(10, 0))
    assert len(scheduled) == 2
    first, second = scheduled
    # First task fills the day
    assert first['start_time'].time() == time(9, 0)
    assert first['end_time'].time() == time(10, 0)
    # Second task should roll to next day's start
    next_day = first['start_time'].date() + timedelta(days=1)
    assert second['start_time'] == datetime.combine(next_day, time(9, 0))
    assert second['end_time'] == second['start_time'] + timedelta(minutes=45)


def test_schedule_tasks_rolls_over_when_end_exceeds_work_end():
    tasks = [
        {'id': 1, 'title': 'Task A', 'type': 'homework', 'estimated_duration': 50, 'due_date': None},
        {'id': 2, 'title': 'Task B', 'type': 'study', 'estimated_duration': 30, 'due_date': None},
    ]
    scheduled = schedule_tasks(tasks, [], work_start=time(9, 0), work_end=time(10, 0))
    assert len(scheduled) == 2
    first, second = scheduled
    # First task takes most of the day
    assert first['start_time'].time() == time(9, 0)
    assert first['end_time'].time() == time(9, 50)
    # Second task cannot finish before work_end, so it should roll to next day
    next_day = first['start_time'].date() + timedelta(days=1)
    assert second['start_time'] == datetime.combine(next_day, time(9, 0))
    assert second['end_time'] == second['start_time'] + timedelta(minutes=30)
