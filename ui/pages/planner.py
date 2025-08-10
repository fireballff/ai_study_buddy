from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
from agents.planner import schedule_tasks
from integrations.google_calendar import GoogleCalendarClient
from sqlalchemy import text


class PlannerPage(QWidget):
    """
    Page for generating and displaying a plan of tasks (today-focused for now).
    """
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine

        layout = QVBoxLayout(self)

        title = QLabel("Planner")
        title.setObjectName("page-title")
        layout.addWidget(title)

        self.plan_btn = QPushButton("Generate Plan for Today")
        self.plan_btn.clicked.connect(self.on_generate)
        layout.addWidget(self.plan_btn)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        layout.addStretch(1)

    def on_generate(self):
        """
        Fetch pending tasks + today's events, compute a schedule, persist, and render.
        """
        tasks = []
        events = []

        # 1) Load pending tasks
        with self.engine.begin() as conn:
            task_rows = conn.execute(
                text(
                    "SELECT id, title, type, estimated_duration, due_date, start_time, end_time "
                    "FROM tasks WHERE state = 'pending'"
                )
            ).fetchall()

            for row in task_rows:
                task_id, title, ttype, duration, due_iso, start_iso, end_iso = row
                task = {
                    "id": task_id,
                    "title": title,
                    "type": ttype,
                    "estimated_duration": duration,
                    "due_date": datetime.fromisoformat(due_iso) if due_iso else None,
                }
                if start_iso and end_iso:
                    task["start_time"] = datetime.fromisoformat(start_iso)
                    task["end_time"] = datetime.fromisoformat(end_iso)
                tasks.append(task)

        # 2) Load today's events from local DB (client stub wraps DB reads)
        events_client = GoogleCalendarClient(self.engine)
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        tomorrow = today_start + timedelta(days=1)
        events = events_client.list_events(today_start, tomorrow)

        # 3) Schedule tasks around events
        scheduled = schedule_tasks(tasks, events)

        # 4) Persist the schedule back to DB
        with self.engine.begin() as conn:
            for t in scheduled:
                conn.execute(
                    text("UPDATE tasks SET start_time = :start, end_time = :end WHERE id = :id"),
                    {
                        "start": t["start_time"].isoformat(),
                        "end": t["end_time"].isoformat(),
                        "id": t["id"],
                    },
                )

        # 5) Show the plan
        self.render_schedule(scheduled)

    def render_schedule(self, tasks: list[dict]):
        self.list_widget.clear()
        tasks_sorted = sorted(tasks, key=lambda t: t["start_time"])
        for t in tasks_sorted:
            start_str = t["start_time"].strftime("%H:%M")
            end_str = t["end_time"].strftime("%H:%M")
            item_text = f"{start_str} → {end_str} — {t['title']} ({t['type']})"
            self.list_widget.addItem(QListWidgetItem(item_text))
