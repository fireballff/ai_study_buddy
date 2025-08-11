from __future__ import annotations
from agents.task_breakdown import breakdown_task


def test_breakdown_large_task():
    task = {
        'title': 'Study Physics',
        'estimated_duration': 120,
        'type': 'study',
    }
    parts = breakdown_task(task)
    assert len(parts) == 2
    assert parts[0]['estimated_duration'] + parts[1]['estimated_duration'] == 120
    assert parts[0]['title'].endswith('(part 1)')


def test_breakdown_small_task():
    task = {
        'title': 'Read article',
        'estimated_duration': 30,
        'type': 'homework',
    }
    parts = breakdown_task(task)
    assert parts == []


def test_short_study_task_no_split():
    task = {
        'title': 'Quick study session',
        'estimated_duration': 20,
        'type': 'study',
    }
    parts = breakdown_task(task)
    assert parts == []


def test_short_project_task_no_split():
    task = {
        'title': 'Minor project prep',
        'estimated_duration': 45,
        'type': 'project',
    }
    parts = breakdown_task(task)
    assert parts == []
