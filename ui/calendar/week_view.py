from __future__ import annotations
from datetime import date, datetime, timedelta, time
from typing import Dict
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt, QDate, QTime, QEvent
from sqlalchemy.engine import Engine

from .calendar_model import CalendarModel, CalendarItem
from .month_view import MonthView
from .quick_add_dialog import QuickAddDialog
from .quick_add_inline import QuickAddInline
from .hover_card import HoverCard
from .conflicts import TimeRange, find_conflicts


class WeekView(QWidget):
    """Minimal 7-day calendar surface with keyboard shortcuts."""

    def __init__(self, engine: Engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.model = CalendarModel(engine)
        self.current_day = datetime.now().date()
        self.selected_item: CalendarItem | None = None
        self._cell_items: Dict[tuple[int, int], CalendarItem] = {}
        self._drag_item: CalendarItem | None = None
        self._drag_start: tuple[int, int] | None = None
        self._resize_edge: str | None = None
        self._conflict_ids: set[int] = set()

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
        self.table.setMouseTracking(True)
        self.table.viewport().installEventFilter(self)
        layout.addWidget(self.table, 1)

        self.quick_inline = QuickAddInline(engine, self.table.viewport())
        self.quick_inline.saved.connect(self.refresh)
        self.hover_card = HoverCard(engine, self.table.viewport())

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
        self._conflict_ids.clear()
        for col in range(7):
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem((week_start + timedelta(days=col)).strftime("%a %d")))
        for day, items in items_by_day.items():
            col = (day - week_start).days
            ranges = [TimeRange(i.start, i.end) for i in items]
            conflicts = find_conflicts(ranges)
            conflicted = {i for pair in conflicts for i in pair}
            for idx, item in enumerate(items):
                row = item.start.hour
                cell = self.table.item(row, col)
                text = item.title
                if cell:
                    cell.setText(cell.text() + " / " + text)
                else:
                    cell = QTableWidgetItem(text)
                    self.table.setItem(row, col, cell)
                if idx in conflicted:
                    cell.setBackground(Qt.red)
                    cell.setToolTip("Overlaps with another item")
                    self._conflict_ids.add(item.id)
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
            if (
                self.selected_item.table == "events"
                and self.selected_item.source == "app"
            ):
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

    # ----- drag & drop / resize -----
    def eventFilter(self, source, event):  # type: ignore[override]
        if source is self.table.viewport():
            if event.type() == QEvent.MouseMove:
                pos = event.position().toPoint()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())
                item = self._cell_items.get((row, col))
                if item:
                    rect = self.table.visualRect(self.table.model().index(row, col))
                    global_pos = self.table.viewport().mapToGlobal(rect.topRight())
                    self.hover_card.show_item(item, conflict=item.id in self._conflict_ids, pos=global_pos)
                else:
                    self.hover_card.hide_card()
                return False
            if event.type() == QEvent.Leave:
                self.hover_card.hide_card()
                return False
            if event.type() == QEvent.MouseButtonDblClick:
                pos = event.position().toPoint()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())
                if (row, col) not in self._cell_items and row >= 0 and col >= 0:
                    day = self.week_start() + timedelta(days=col)
                    start_dt = datetime.combine(day, time(row))
                    rect = self.table.visualRect(self.table.model().index(row, col))
                    self.quick_inline.start(rect, start_dt)
                    return True
            if event.type() == QEvent.MouseButtonPress:
                pos = event.position().toPoint()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())
                item = self._cell_items.get((row, col))
                if not item:
                    return False
                self.selected_item = item
                self._drag_item = item
                self._drag_start = (row, col)
                rect = self.table.visualRect(self.table.model().index(row, col))
                margin = 5
                if abs(pos.y() - rect.top()) <= margin:
                    self._resize_edge = "start"
                elif abs(pos.y() - rect.bottom()) <= margin:
                    self._resize_edge = "end"
                else:
                    self._resize_edge = None
                return True
            if event.type() == QEvent.MouseButtonRelease and self._drag_item:
                pos = event.position().toPoint()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())
                if row < 0 or col < 0 or self._drag_start is None:
                    self._drag_item = None
                    self._resize_edge = None
                    return False
                drow = row - self._drag_start[0]
                dcol = col - self._drag_start[1]
                start = self._drag_item.start
                end = self._drag_item.end
                if self._resize_edge == "start":
                    new_start = start + timedelta(days=dcol, hours=drow)
                    new_end = end
                elif self._resize_edge == "end":
                    new_start = start
                    new_end = end + timedelta(days=dcol, hours=drow)
                else:
                    new_start = start + timedelta(days=dcol, hours=drow)
                    new_end = end + timedelta(days=dcol, hours=drow)
                self.model.update_item_time(self._drag_item, new_start, new_end)
                self._drag_item = None
                self._resize_edge = None
                self.refresh()
                return True
        return super().eventFilter(source, event)
