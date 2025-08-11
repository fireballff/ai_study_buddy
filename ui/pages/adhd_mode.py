from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem
from PyQt6.QtCore import QTimer, Qt
from datetime import datetime
from sqlalchemy import text
from project.db import get_engine


class ADHDModePage(QWidget):
    """
    Focus mode with Pomodoro timers and simplified task list.
    """
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        layout = QVBoxLayout(self)
        self.setWindowTitle("Focus Mode")

        title = QLabel("Focus Mode")
        title.setObjectName("page-title")
        layout.addWidget(title)

        # Timer display
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 32px; padding: 16px;")
        layout.addWidget(self.timer_label)

        # Buttons
        self.start_btn = QPushButton("Start 25/5")
        self.start_btn.clicked.connect(self.start_timer)
        layout.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Stop Timer")
        self.stop_btn.clicked.connect(self.stop_timer)
        layout.addWidget(self.stop_btn)

        # Task list
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        layout.addStretch(1)

        # Timer internals
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.current_phase = "idle"
        self.remaining_seconds = 0

    def refresh_tasks(self):
        self.list_widget.clear()
        with self.engine.begin() as conn:
            rows = conn.execute(
                text(
                    "SELECT id, title, type, start_time, end_time FROM tasks WHERE state = 'pending' ORDER BY start_time"
                )
            ).fetchall()
            for row in rows:
                id_, title, ttype, start, end = row
                time_str = ""
                if start and end:
                    time_str = f" | {start} → {end}"
                item_text = f"{title} ({ttype}){time_str}"
                self.list_widget.addItem(QListWidgetItem(item_text))

    def start_timer(self):
        if self.current_phase == "work":
            return
        # Start work phase (25 min)
        self.current_phase = "work"
        self.remaining_seconds = 25 * 60
        self.update_timer_label()
        self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()
        self.current_phase = "idle"
        self.remaining_seconds = 0
        self.update_timer_label()

    def tick(self):
        if self.remaining_seconds <= 0:
            if self.current_phase == "work":
                # switch to break
                self.current_phase = "break"
                self.remaining_seconds = 5 * 60
            elif self.current_phase == "break":
                self.current_phase = "work"
                self.remaining_seconds = 25 * 60
            else:
                self.timer.stop()
                return
        else:
            self.remaining_seconds -= 1
        self.update_timer_label()

    def update_timer_label(self):
        if self.current_phase == "idle":
            self.timer_label.setText("00:00")
        else:
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            phase_name = "Work" if self.current_phase == "work" else "Break"
            self.timer_label.setText(f"{phase_name} {minutes:02d}:{seconds:02d}")
