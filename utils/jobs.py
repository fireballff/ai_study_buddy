from __future__ import annotations
from enum import Enum
from typing import Any, Callable, Dict

class JobType(str, Enum):
    PLAN_WEEK = "plan_week"
    SYNC_APP_EVENTS = "sync_app_events"

JobHandler = Callable[[Any], None]

JOB_HANDLERS: Dict[JobType, JobHandler] = {}

def register(job_type: JobType) -> Callable[[JobHandler], JobHandler]:
    """Decorator to register a function as a job handler."""
    def decorator(func: JobHandler) -> JobHandler:
        JOB_HANDLERS[job_type] = func
        return func
    return decorator

@register(JobType.PLAN_WEEK)
def plan_week(payload: Any) -> None:
    """Placeholder planning job."""
    pass

@register(JobType.SYNC_APP_EVENTS)
def sync_app_events(payload: Any) -> None:
    """Placeholder sync job."""
    pass
