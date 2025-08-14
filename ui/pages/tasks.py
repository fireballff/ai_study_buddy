from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QLineEdit,
)
from PyQt6.QtCore import QTimer
from datetime import datetime
import uuid

from project.repo.base import Task
from project.repo.syncing import SyncingRepo
from project.repo.query_builders import build_tasks_query  # re-export for tests

__all__ = ["build_tasks_query", "TasksPage"]


class TasksPage(QWidget):
    """Page to display and manage user tasks with filters and search."""

    def __init__(self, repo: SyncingRepo, parent=None):
        super().__init__(parent)
        self.repo = repo
        layout = QVBoxLayout(self)
        title = QLabel("Tasks")
        title.setObjectName("page-title")
        layout.addWidget(title)

        self.add_btn = QPushButton("Add Task")
        self.add_btn.clicked.connect(self.on_add_task)
        layout.addWidget(self.add_btn)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Today", "Upcoming", "By Course", "By Priority", "All"])
        self.filter_combo.currentTextChanged.connect(self.refresh_list)
        layout.addWidget(self.filter_combo)

        self.search_edit = QLineEdit()
        layout.addWidget(self.search_edit)
        self.search_timer = QTimer(self)
        self.search_timer.setInterval(250)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.refresh_list)
        self.search_edit.textChanged.connect(lambda: self.search_timer.start())

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        layout.addStretch(1)
        self.refresh_list()

    # ------------------------------------------------------------------
    def refresh_list(self):
        """Load tasks from repo and display them in the list widget."""
        self.list_widget.clear()
        filter_mode = self.filter_combo.currentText() if hasattr(self, "filter_combo") else "All"
        search = self.search_edit.text() if hasattr(self, "search_edit") else ""
        tasks = self.repo.list_tasks(filter_mode, search)
        for t in tasks:
            parts = [f"#{t.id} [{t.state}] {t.title} ({t.type}, {t.estimated_duration}m)"]
            if t.course_label:
                parts.append(f"• {t.course_label}")
            if t.priority is not None:
                parts.append(f"• p{t.priority}")
            if t.due_date:
                try:
                    due_disp = datetime.fromisoformat(t.due_date).date().isoformat()
                except Exception:
                    due_disp = t.due_date
                parts.append(f"– due {due_disp}")
            if t.start_time and t.end_time:
                try:
                    start_t = datetime.fromisoformat(t.start_time).strftime("%H:%M")
                    end_t = datetime.fromisoformat(t.end_time).strftime("%H:%M")
                    parts.append(f"| {start_t}→{end_t}")
                except Exception:
                    pass
            item_text = " ".join(parts)
            self.list_widget.addItem(QListWidgetItem(item_text))

    # ------------------------------------------------------------------
    def on_add_task(self):
        from PyQt6.QtWidgets import (
            QDialog,
            QFormLayout,
            QLineEdit,
            QDialogButtonBox,
            QComboBox,
            QDateTimeEdit,
            QSpinBox,
            QCheckBox,
        )
        from agents import classifier

        dialog = QDialog(self)
        dialog.setWindowTitle("New Task")
        layout = QFormLayout(dialog)
        title_edit = QLineEdit()
        layout.addRow("Title", title_edit)
        type_combo = QComboBox()
        type_combo.addItem("")
        type_combo.addItems(["homework", "study", "test", "class", "meeting", "project"])
        layout.addRow("Type", type_combo)
        duration_spin = QSpinBox()
        duration_spin.setRange(15, 480)
        duration_spin.setValue(60)
        layout.addRow("Estimated Duration (min)", duration_spin)
        due_checkbox = QCheckBox("Set Due Date")
        due_edit = QDateTimeEdit()
        due_edit.setCalendarPopup(True)
        due_edit.setDateTime(datetime.now())
        due_edit.setEnabled(False)
        due_checkbox.toggled.connect(due_edit.setEnabled)
        layout.addRow(due_checkbox, due_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addRow(buttons)

        def accept():
            title = title_edit.text().strip()
            if not title:
                return
            ttype = type_combo.currentText().strip()
            duration = duration_spin.value()
            if due_checkbox.isChecked():
                due_dt = due_edit.dateTime().toPyDateTime()
                due_iso = due_dt.isoformat()
            else:
                due_iso = None
            classification = classifier.classify(title)
            if not ttype:
                ttype = classification["type"]
            course_label = classification.get("course_label")
            priority = classification.get("priority", 0)
            task = Task(
                id=None,
                owner_user_id=None,
                source="app",
                source_id=str(uuid.uuid4()),
                title=title,
                type=ttype,
                estimated_duration=duration,
                due_date=due_iso,
                course_label=course_label,
                priority=priority,
            )
            self.repo.upsert_task(task)
            dialog.accept()
            self.refresh_list()

        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()
