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
from datetime import datetime, timedelta
from sqlalchemy import text
from agents import classifier


def build_tasks_query(filter_mode: str, search: str):
    """Construct the SQL query and parameters for a tasks view."""
    where_clauses = []
    params: dict[str, str] = {}

    if filter_mode == "Today":
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        params["today"] = today.isoformat()
        params["tomorrow"] = tomorrow.isoformat()
        where_clauses.append(
            "(state = 'pending' OR (start_time >= :today AND start_time < :tomorrow))"
        )
        order_clause = "ORDER BY COALESCE(start_time, due_date)"
    elif filter_mode == "Upcoming":
        where_clauses.append("due_date IS NOT NULL")
        order_clause = "ORDER BY due_date"
    elif filter_mode == "By Course":
        order_clause = "ORDER BY COALESCE(course_label, ''), COALESCE(due_date, '9999-12-31')"
    elif filter_mode == "By Priority":
        order_clause = "ORDER BY COALESCE(priority, 3), COALESCE(due_date, '9999-12-31')"
    else:  # All
        order_clause = "ORDER BY created_at"

    if search:
        params["q"] = f"%{search.lower()}%"
        where_clauses.append(
            "(LOWER(title) LIKE :q OR LOWER(type) LIKE :q OR LOWER(COALESCE(course_label,'')) LIKE :q)"
        )

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = (
        "SELECT id, title, type, estimated_duration, due_date, state, start_time, end_time, "
        "course_label, priority FROM tasks "
        f"{where_sql} {order_clause}"
    )
    return sql, params


class TasksPage(QWidget):
    """Page to display and manage user tasks with filters and search."""

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
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

    def refresh_list(self):
        """Load tasks from DB and display them in the list widget."""
        self.list_widget.clear()
        filter_mode = self.filter_combo.currentText() if hasattr(self, "filter_combo") else "All"
        search = self.search_edit.text() if hasattr(self, "search_edit") else ""
        sql, params = build_tasks_query(filter_mode, search)
        self.list_widget.clear()
        with self.engine.begin() as conn:
            rows = conn.execute(text(sql), params).fetchall()
            for row in rows:
                task_id, title, ttype, duration, due, state, start, end, course, priority = row
                parts = [f"#{task_id} [{state}] {title} ({ttype}, {duration}m)"]
                if course:
                    parts.append(f"• {course}")
                if priority is not None:
                    parts.append(f"• p{priority}")
                if due:
                    try:
                        due_disp = datetime.fromisoformat(due).date().isoformat()
                    except Exception:
                        due_disp = due
                    parts.append(f"– due {due_disp}")
                if start and end:
                    try:
                        start_t = datetime.fromisoformat(start).strftime("%H:%M")
                        end_t = datetime.fromisoformat(end).strftime("%H:%M")
                        parts.append(f"| {start_t}→{end_t}")
                    except Exception:
                        pass
                item_text = " ".join(parts)
                self.list_widget.addItem(QListWidgetItem(item_text))

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
            priority = classification.get("priority")
            # Insert into DB
            with self.engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO tasks (title, type, estimated_duration, due_date, course_label, priority) VALUES (:title, :type, :duration, :due, :course, :priority)"
                    ),
                    {"title": title, "type": ttype, "duration": duration, "due": due_iso, "course": course_label, "priority": priority},
                )
            dialog.accept()
            self.refresh_list()

        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()
