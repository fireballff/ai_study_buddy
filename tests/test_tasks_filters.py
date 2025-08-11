from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from ui.pages.tasks import build_tasks_query


def setup_engine(rows):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    estimated_duration INTEGER NOT NULL,
                    due_date TEXT,
                    course_label TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    state TEXT NOT NULL,
                    priority INTEGER,
                    created_by TEXT
                )
                """
            )
        )
        for row in rows:
            conn.execute(
                text(
                    """
                    INSERT INTO tasks
                    (title, type, estimated_duration, due_date, course_label, created_at, start_time, end_time, state, priority)
                    VALUES (:title, :type, :estimated_duration, :due_date, :course_label, :created_at, :start_time, :end_time, :state, :priority)
                    """
                ),
                row,
            )
    return engine


def run_query(engine, filter_mode, search=""):
    sql, params = build_tasks_query(filter_mode, search)
    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).fetchall()
    return [r[0] for r in rows]


def test_filter_today_includes_pending_and_todays_scheduled():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    rows = [
        {
            "title": "Pending",
            "type": "study",
            "estimated_duration": 60,
            "due_date": None,
            "course_label": None,
            "created_at": "2024-01-01T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "Today Event",
            "type": "class",
            "estimated_duration": 60,
            "due_date": None,
            "course_label": None,
            "created_at": "2024-01-02T00:00:00",
            "start_time": (today + timedelta(hours=9)).isoformat(),
            "end_time": (today + timedelta(hours=10)).isoformat(),
            "state": "done",
            "priority": None,
        },
        {
            "title": "Pending Tomorrow",
            "type": "class",
            "estimated_duration": 60,
            "due_date": None,
            "course_label": None,
            "created_at": "2024-01-03T00:00:00",
            "start_time": (tomorrow + timedelta(hours=9)).isoformat(),
            "end_time": (tomorrow + timedelta(hours=10)).isoformat(),
            "state": "pending",
            "priority": None,
        },
        {
            "title": "Tomorrow Event",
            "type": "class",
            "estimated_duration": 60,
            "due_date": None,
            "course_label": None,
            "created_at": "2024-01-04T00:00:00",
            "start_time": (tomorrow + timedelta(hours=11)).isoformat(),
            "end_time": (tomorrow + timedelta(hours=12)).isoformat(),
            "state": "done",
            "priority": None,
        },
    ]
    engine = setup_engine(rows)
    ids = run_query(engine, "Today")
    assert ids == [1, 2, 3]


def test_filter_upcoming_by_due_date_only():
    base = datetime.now().date()
    rows = [
        {
            "title": "Due1",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=1)).isoformat(),
            "course_label": None,
            "created_at": "2024-01-01T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "Due2",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=2)).isoformat(),
            "course_label": None,
            "created_at": "2024-01-02T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "NoDue",
            "type": "study",
            "estimated_duration": 30,
            "due_date": None,
            "course_label": None,
            "created_at": "2024-01-03T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
    ]
    engine = setup_engine(rows)
    ids = run_query(engine, "Upcoming")
    assert ids == [1, 2]


def test_filter_by_course_sorts_grouped():
    base = datetime.now().date()
    rows = [
        {
            "title": "NoCourse",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=5)).isoformat(),
            "course_label": None,
            "created_at": "2024-01-01T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "BioB",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=2)).isoformat(),
            "course_label": "BIO",
            "created_at": "2024-01-02T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "BioA",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=1)).isoformat(),
            "course_label": "BIO",
            "created_at": "2024-01-03T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "Math",
            "type": "study",
            "estimated_duration": 30,
            "due_date": None,
            "course_label": "MATH",
            "created_at": "2024-01-04T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
    ]
    engine = setup_engine(rows)
    ids = run_query(engine, "By Course")
    assert ids == [1, 3, 2, 4]


def test_filter_by_priority_orders_correctly():
    base = datetime.now().date()
    rows = [
        {
            "title": "P1 later",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=4)).isoformat(),
            "course_label": None,
            "created_at": "2024-01-01T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": 1,
        },
        {
            "title": "P2",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=2)).isoformat(),
            "course_label": None,
            "created_at": "2024-01-02T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": 2,
        },
        {
            "title": "Pnull",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=3)).isoformat(),
            "course_label": None,
            "created_at": "2024-01-03T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "P1 sooner",
            "type": "study",
            "estimated_duration": 30,
            "due_date": (base + timedelta(days=1)).isoformat(),
            "course_label": None,
            "created_at": "2024-01-04T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": 1,
        },
    ]
    engine = setup_engine(rows)
    ids = run_query(engine, "By Priority")
    assert ids == [4, 1, 2, 3]


def test_search_matches_title_type_course():
    rows = [
        {
            "title": "Read Book",
            "type": "study",
            "estimated_duration": 30,
            "due_date": None,
            "course_label": "ENG",
            "created_at": "2024-01-01T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "Essay",
            "type": "homework",
            "estimated_duration": 30,
            "due_date": None,
            "course_label": "MATH",
            "created_at": "2024-01-02T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
    ]
    engine = setup_engine(rows)
    assert run_query(engine, "All", "read") == [1]
    assert run_query(engine, "All", "homework") == [2]
    assert run_query(engine, "All", "eng") == [1]


def test_all_shows_everything():
    rows = [
        {
            "title": "A",
            "type": "study",
            "estimated_duration": 30,
            "due_date": None,
            "course_label": None,
            "created_at": "2024-01-01T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
        {
            "title": "B",
            "type": "study",
            "estimated_duration": 30,
            "due_date": None,
            "course_label": None,
            "created_at": "2024-01-02T00:00:00",
            "start_time": None,
            "end_time": None,
            "state": "pending",
            "priority": None,
        },
    ]
    engine = setup_engine(rows)
    ids = run_query(engine, "All")
    assert ids == [1, 2]
