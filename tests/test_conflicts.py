from datetime import datetime, timedelta
from ui.calendar.conflicts import TimeRange, find_conflicts


BASE = datetime(2024, 1, 1)

def tr(start_hour: int, end_hour: int) -> TimeRange:
    return TimeRange(BASE + timedelta(hours=start_hour), BASE + timedelta(hours=end_hour))


def test_edge_touching_not_conflict():
    ranges = [tr(8, 9), tr(9, 10)]
    assert find_conflicts(ranges) == []


def test_simple_conflict_pair():
    ranges = [tr(9, 11), tr(10, 12), tr(12, 13)]
    assert find_conflicts(ranges) == [(0, 1)]


def test_multiple_conflicts_chain():
    ranges = [tr(9, 11), tr(10, 12), tr(11, 13), tr(12, 14)]
    assert find_conflicts(ranges) == [(0, 1), (1, 2), (2, 3)]
