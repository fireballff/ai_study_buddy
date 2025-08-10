from __future__ import annotations
from datetime import datetime, time
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