from datetime import datetime
from integrations.google_calendar import GoogleCalendarClient
from project.db import get_engine, ensure_db
from sqlalchemy import text


def test_list_events_overlapping_edges(tmp_path):
    db_path = tmp_path / "test.db"
    engine = get_engine(str(db_path))
    ensure_db(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO events (source, source_id, title, start_time, end_time, type, description) "
                "VALUES (:source, :source_id, :title, :start_time, :end_time, :type, :description)"
            ),
            [
                {
                    "source": "local",
                    "source_id": "ev1",
                    "title": "OverlapStart",
                    "start_time": "2024-01-01T08:00:00",
                    "end_time": "2024-01-01T09:30:00",
                    "type": "meeting",
                    "description": "",
                },
                {
                    "source": "local",
                    "source_id": "ev2",
                    "title": "OverlapEnd",
                    "start_time": "2024-01-01T09:30:00",
                    "end_time": "2024-01-01T10:30:00",
                    "type": "meeting",
                    "description": "",
                },
                {
                    "source": "local",
                    "source_id": "ev3",
                    "title": "Outside",
                    "start_time": "2024-01-01T11:00:00",
                    "end_time": "2024-01-01T12:00:00",
                    "type": "meeting",
                    "description": "",
                },
            ],
        )
    client = GoogleCalendarClient(engine)
    start = datetime.fromisoformat("2024-01-01T09:00:00")
    end = datetime.fromisoformat("2024-01-01T10:00:00")
    events = client.list_events(start, end)
    titles = {e["title"] for e in events}
    assert "OverlapStart" in titles
    assert "OverlapEnd" in titles
    assert "Outside" not in titles
    assert len(events) == 2
