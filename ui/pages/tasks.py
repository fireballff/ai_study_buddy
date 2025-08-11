from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
)
from datetime import datetime
from sqlalchemy import text
from agents import classifier


class TasksPage(QWidget):
    """
    Page to display and manage user tasks. Allows adding tasks and viewing existing ones.
    """
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

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        layout.addStretch(1)
        self.refresh_list()

    def refresh_list(self):
        """Load tasks from DB and display them in the list widget."""
        self.list_widget.clear()
        with self.engine.begin() as conn:
            rows = conn.execute(
                text(
                    "SELECT id, title, type, estimated_duration, due_date, state, start_time, end_time, course_label, priority FROM tasks ORDER BY created_at"
                )
            ).fetchall()
            for row in rows:
                task_id, title, ttype, duration, due, state, start, end, course, priority = row
                due_str = f"Due: {due}" if due else ""
                state_str = f"[{state}]"
                time_str = ""
                if start and end:
                    time_str = f" | {start} → {end}"
                course_str = f"[{course}]" if course else ""
                priority_str = f"P{priority}" if priority is not None else ""
                item_text = f"#{task_id}: {title} {course_str} {priority_str} ({ttype}, {duration}m) {state_str} {due_str}{time_str}"
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
