from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
from project.db import get_engine
from agents.planner import schedule_tasks
from integrations.google_calendar import GoogleCalendarClient


class PlannerPage(QWidget):
    """
    Page for generating and displaying a weekly plan of tasks.
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
        Trigger planning: fetch tasks and events from DB and compute schedule.
        """
        tasks = []
        events = []
        with self.engine.begin() as conn:
            # fetch tasks that are pending
            task_rows = conn.execute(
                "SELECT id, title, type, estimated_duration, due_date, start_time, end_time FROM tasks WHERE state = 'pending'"
            ).fetchall()
            for row in task_rows:
                id_, title, ttype, duration, due_iso, start, end = row
                task = {
                    'id': id_,
                    'title': title,
                    'type': ttype,
                    'estimated_duration': duration,
                    'due_date': datetime.fromisoformat(due_iso) if due_iso else None,
                }
                if start and end:
                    task['start_time'] = datetime.fromisoformat(start)
                    task['end_time'] = datetime.fromisoformat(end)
                tasks.append(task)
            # fetch events (use local DB via GoogleCalendarClient stub)
            events_client = GoogleCalendarClient(self.engine)
            # For now, we fetch events for today
            today_start = datetime.combine(datetime.now().date(), datetime.min.time())
            tomorrow = today_start + timedelta(days=1)
            events = events_client.list_events(today_start, tomorrow)
        # schedule tasks around events
        scheduled = schedule_tasks(tasks, events)
        # update tasks in DB
        with self.engine.begin() as conn:
            for t in scheduled:
                conn.execute(
                    "UPDATE tasks SET start_time = :start, end_time = :end WHERE id = :id",
                    {
                        'start': t['start_time'].isoformat(),
                        'end': t['end_time'].isoformat(),
                        'id': t['id'],
                    },
                )
        # Display schedule
        self.render_schedule(scheduled)

    def render_schedule(self, tasks: list):
        self.list_widget.clear()
        tasks_sorted = sorted(tasks, key=lambda t: t['start_time'])
        for t in tasks_sorted:
            item_text = f"{t['start_time'].strftime('%H:%M')} → {t['end_time'].strftime('%H:%M')} — {t['title']} ({t['type']})"
            self.list_widget.addItem(QListWidgetItem(item_text))