from datetime import datetime

from ui.calendar.quick_add_inline import parse_inline


def test_parse_hw_example():
    base = datetime(2024, 1, 1, 9, 0)  # Monday
    result = parse_inline("Math HW 30m @ Tue 3pm #MATH203", base)
    assert result["title"] == "Math HW"
    assert result["start"] == datetime(2024, 1, 2, 15, 0)
    assert result["end"] == datetime(2024, 1, 2, 15, 30)
    assert result["type"] == "homework"
    assert result["course"] == "MATH203"


def test_parse_study_example():
    base = datetime(2024, 1, 1, 9, 0)
    result = parse_inline("Study BIO210 50m tomorrow 10:00", base)
    assert result["title"] == "Study BIO210"
    assert result["start"] == datetime(2024, 1, 2, 10, 0)
    assert result["end"] == datetime(2024, 1, 2, 10, 50)
    assert result["type"] == "study"
    assert result["course"] == "BIO210"
