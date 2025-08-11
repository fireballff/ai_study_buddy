from agents.classifier import classify


def test_midterm_detects_test_and_priority_1():
    result = classify("Midterm exam for CS101")
    assert result["type"] == "test"
    assert result["priority"] == 1


def test_homework_detects_homework_priority_2():
    result = classify("Homework assignment")
    assert result["type"] == "homework"
    assert result["priority"] == 2


def test_course_label_extraction_cs101():
    result = classify("Study for CS101")
    assert result["course_label"] == "CS101"


def test_default_rule_returns_study_priority_3():
    result = classify("Go for a walk")
    assert result["type"] == "study"
    assert result["priority"] == 3
