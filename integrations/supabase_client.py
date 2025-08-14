"""Supabase client helper with basic retry/backoff."""
from __future__ import annotations

from typing import Any, Optional
import time
import logging

from supabase import Client, create_client
from project.settings import Settings

_logger = logging.getLogger(__name__)
_client: Optional[Client] = None


def get_client(settings: Settings) -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise RuntimeError("Supabase credentials missing")
        _client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _client


def _retry(fn, *args, **kwargs):
    delay = 1.0
    for attempt in range(3):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - network failures
            _logger.warning("supabase_request_error", extra={"attempt": attempt + 1, "error": str(exc)})
            if attempt == 2:
                raise
            time.sleep(delay)
            delay *= 2


class SupabaseClient:
    """Typed helper wrapping basic CRUD operations."""

    def __init__(self, client: Client):
        self._client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseClient":
        return cls(get_client(settings))

    # ---- tasks ---------------------------------------------------------
    def upsert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        return _retry(self._client.table(table).upsert, payload).data

    def delete(self, table: str, column: str, value: Any) -> None:
        _retry(self._client.table(table).delete().eq, column, value)

    def select(self, table: str, query: str, **filters: Any) -> list[dict[str, Any]]:
        tbl = self._client.table(table).select(query)
        for key, val in filters.items():
            tbl = tbl.eq(key, val)
        return _retry(tbl.execute).data
