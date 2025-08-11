from __future__ import annotations
from dataclasses import dataclass
from datetime import time
from typing import Optional

from .settings import load_settings, Settings


@dataclass
class UserPrefs:
    day_start: time = time(8, 0)
    day_end: time = time(22, 0)
    default_session_minutes: int = 50
    max_sessions_per_day: int = 6


def _parse_time(value: Optional[str]) -> Optional[time]:
    if value is None:
        return None
    if isinstance(value, time):
        return value
    try:
        hour, minute = map(int, str(value).split(":"))
        return time(hour, minute)
    except Exception:
        return None


def load_prefs(settings: Optional[Settings] = None) -> UserPrefs:
    settings = settings or load_settings()
    start = _parse_time(getattr(settings, "day_start", None)) or UserPrefs.day_start
    end = _parse_time(getattr(settings, "day_end", None)) or UserPrefs.day_end
    default_minutes = getattr(settings, "default_session_minutes", UserPrefs.default_session_minutes)
    max_sessions = getattr(settings, "max_sessions_per_day", UserPrefs.max_sessions_per_day)
    return UserPrefs(day_start=start, day_end=end, default_session_minutes=default_minutes, max_sessions_per_day=max_sessions)
