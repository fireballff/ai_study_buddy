from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class TimeRange:
    """Simple start/end container used for conflict detection."""
    start: datetime
    end: datetime

    def overlaps(self, other: "TimeRange") -> bool:
        """Return True if two ranges overlap.

        Endpoints touching (end == start) do not count as a conflict.
        """
        return self.start < other.end and other.start < self.end


def find_conflicts(ranges: Iterable[TimeRange]) -> List[Tuple[int, int]]:
    """Return index pairs of overlapping ranges.

    The returned list is sorted in the order the conflicts are discovered.
    Each pair represents the indexes of two ranges that overlap.
    """
    items = list(ranges)
    conflicts: List[Tuple[int, int]] = []
    for i, a in enumerate(items):
        for j in range(i + 1, len(items)):
            if a.overlaps(items[j]):
                conflicts.append((i, j))
    return conflicts
