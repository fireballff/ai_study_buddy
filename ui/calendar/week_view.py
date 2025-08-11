from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Dict
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt, QDate, QTime
from sqlalchemy.engine import Engine

from .calendar_model import CalendarModel, CalendarItem
from .month_view import MonthView
from .quick_add_dialog import QuickAddDialog


class WeekView(QWidget):
    """Minimal 7-day calendar surface with keyboard shortcuts."""

    def __init__(self, engine: Engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.model = CalendarModel(engine)
        self.current_day = datetime.now().date()
        self.selected_item: CalendarItem | None = None
        self._cell_items: Dict[tuple[int, int], CalendarItem] = {}

        layout = QVBoxLayout(self)
        self.month = MonthView(self)
        self.month.day_selected.connect(self.on_day_selected)
        layout.addWidget(self.month)

        self.table = QTableWidget(24, 7, self)
        self.table.setHorizontalHeaderLabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        hours = [f"{h:02d}:00" for h in range(24)]
        self.table.setVerticalHeaderLabels(hours)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setDefaultSectionSize(120)
        self.table.cellClicked.connect(self.on_cell_clicked)
        layout.addWidget(self.table, 1)

        # apply local styles
        self._load_styles()
        self.refresh()

    # ----- helpers -----
    def _load_styles(self) -> None:
        try:
            from pathlib import Path
            qss = Path(__file__).with_name("styles.qss")
            self.setStyleSheet(qss.read_text())
        except Exception:
            pass

    def week_start(self, day: date | None = None) -> date:
        day = day or self.current_day
        return day - timedelta(days=day.weekday())

    def on_day_selected(self, day: date) -> None:
        self.current_day = day
        self.refresh()

    def refresh(self) -> None:
        week_start = self.week_start()
        week_end = week_start + timedelta(days=6)
        items_by_day = self.model.fetch_range(week_start, week_end)
        self.table.clearContents()
        self._cell_items.clear()
        for col in range(7):
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem((week_start + timedelta(days=col)).strftime("%a %d")))
        for day, items in items_by_day.items():
            col = (day - week_start).days
            for item in items:
                row = item.start.hour
                cell = self.table.item(row, col)
                text = item.title
                if cell:
                    cell.setText(cell.text() + " / " + text)
                else:
                    self.table.setItem(row, col, QTableWidgetItem(text))
                self._cell_items[(row, col)] = item
        # update month badges for current month
        month_start = date(self.current_day.year, self.current_day.month, 1)
        next_month = month_start.replace(day=28) + timedelta(days=4)
        month_end = next_month - timedelta(days=next_month.day)
        counts: Dict[date, int] = {}
        monthly = self.model.fetch_range(month_start, month_end)
        for d, items in monthly.items():
            counts[d] = len(items)
        self.month.set_badges(counts)
        self.month.setSelectedDate(self.current_day)

    # ----- keyboard -----
    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        key = event.key()
        modifiers = event.modifiers()
        if key == Qt.Key_N:
            self.open_quick_add()
            return
        if key == Qt.Key_Delete and self.selected_item:
            self.model.delete_item(self.selected_item)
            self.refresh()
            return
        if key == Qt.Key_E and self.selected_item:
            self.edit_selected()
            return
        if key == Qt.Key_K and (modifiers & Qt.KeyboardModifier.ControlModifier or modifiers & Qt.KeyboardModifier.MetaModifier):
            self.open_quick_add()
            return
        super().keyPressEvent(event)

    def open_quick_add(self) -> None:
        dlg = QuickAddDialog(self.engine, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self.refresh()

    def on_cell_clicked(self, row: int, column: int) -> None:
        self.selected_item = self._cell_items.get((row, column))

    def edit_selected(self) -> None:
        if not self.selected_item:
            return
        dlg = QuickAddDialog(self.engine, self)
        dlg.txt_title.setText(self.selected_item.title)
        qdate = QDate(
            self.selected_item.start.year,
            self.selected_item.start.month,
            self.selected_item.start.day,
        )
        dlg.date.setDate(qdate)
        dlg.start.setTime(QTime(self.selected_item.start.hour, self.selected_item.start.minute))
        dlg.end.setTime(QTime(self.selected_item.end.hour, self.selected_item.end.minute))
        dlg.cmb_type.setCurrentText(self.selected_item.type)
        if dlg.exec() == dlg.DialogCode.Accepted:
            # simple approach: delete old and rely on dialog insert
            self.model.delete_item(self.selected_item)
            self.refresh()
