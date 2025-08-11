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
    """Background job to sync application events.

    ``payload`` expects a ``client`` key containing an instance of
    :class:`integrations.google_calendar.GoogleCalendarClient`.  The client is
    asked to perform an incremental fetch using any provided ``cursor``.  Any
    exception raised bubbles up to the worker which will trigger retry/backoff
    behaviour.
    """
    client = payload.get("client")
    if client is None:
        raise ValueError("sync_app_events requires a 'client' in payload")
    provider = payload.get("provider", "google")
    cursor = payload.get("cursor")
    client.fetch_since(provider, cursor)
