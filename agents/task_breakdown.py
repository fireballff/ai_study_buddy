from __future__ import annotations
from typing import List, Dict


def breakdown_task(task: Dict) -> List[Dict]:
    """
    Break down a complex task into smaller steps.

    For demonstration, tasks with an estimated_duration > 60 minutes or type 'study' or 'project'
    are split into two subtasks of equal duration.
    Returns a list of new task dicts or an empty list if no breakdown needed.
    """
    duration = task.get('estimated_duration', 0)
    ttype = task.get('type', '').lower()
    if duration > 60 or ttype in {'study', 'project'}:
        half = max(30, duration // 2)
        subtask1 = task.copy()
        subtask1['title'] = task['title'] + " (part 1)"
        subtask1['estimated_duration'] = half
        subtask2 = task.copy()
        subtask2['title'] = task['title'] + " (part 2)"
        subtask2['estimated_duration'] = duration - half
        return [subtask1, subtask2]
    return []