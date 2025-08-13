from __future__ import annotations

from datetime import datetime, timedelta, time, date
from typing import Dict, Tuple, Optional, Set

from PyQt6.QtCore import Qt, QDate, QTime, QEvent
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem

from sqlalchemy.engine import Engine

from .calendar_model import CalendarModel, CalendarItem
from .month_view import MonthView
from .quick_add_dialog import QuickAddDialog
from .quick_add_inline import QuickAddInline
from .hover_card import HoverCard
from .conflicts import TimeRange, find_conflicts


class WeekView(QWidget):
    """Minimal 7‑day calendar with inline quick‑add, hover cards, and drag/resize."""

    def __init__(self, engine: Engine, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.model = CalendarModel(engine)

        self.current_day: date = datetime.now().date()
        self.selected_item: Optional[CalendarItem] = None
        self._cell_items: Dict[Tuple[int, int], CalendarItem] = {}
        self._drag_item: Optional[CalendarItem] = None
        self._drag_start: Optional[Tuple[int, int]] = None
        self._resize_edge: Optional[str] = None  # "start" | "end" | None
        self._conflict_ids: Set[int] = set()

        layout = QVBoxLayout(self)

        # Month header with badges + selection
        self.month = MonthView(self)
        self.month.day_selected.connect(self.on_day_selected)
        layout.addWidget(self.month)

        # 24 x 7 grid (hours x weekdays)
        self.table = QTableWidget(24, 7, self)
        self.table.setHorizontalHeaderLabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        self.table.setVerticalHeaderLabels([f"{h:02d}:00" for h in range(24)])

        vh = self.table.verticalHeader()
        if vh is not None:
            vh.setDefaultSectionSize(40)
        hh = self.table.horizontalHeader()
        if hh is not None:
            hh.setDefaultSectionSize(120)

        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.setMouseTracking(True)

        # Cache viewport once; PyQt always returns a QWidget, but we assert for the type checker
        vp = self.table.viewport()
        assert vp is not None
        self._viewport = vp  # QWidget
        self._viewport.installEventFilter(self)

        layout.addWidget(self.table, 1)

        # Overlays
        self.quick_inline = QuickAddInline(engine, self._viewport)
        self.quick_inline.saved.connect(self.refresh)

        self.hover_card = HoverCard(engine, self._viewport)

        # Optional: load QSS next to this file
        self._load_styles()

        self.refresh()

    # ----- helpers -----
    def _load_styles(self) -> None:
        try:
            from pathlib import Path
            qss = Path(__file__).with_name("styles.qss")
            self.setStyleSheet(qss.read_text(encoding="utf-8"))
        except Exception:
            pass

    def week_start(self, day: Optional[date] = None) -> date:
        d = day or self.current_day
        return d - timedelta(days=d.weekday())

    def on_day_selected(self, day: date) -> None:
        self.current_day = day
        self.refresh()

    def refresh(self) -> None:
        start = self.week_start()
        end = start + timedelta(days=6)

        items_by_day = self.model.fetch_range(start, end)

        self.table.clearContents()
        self._cell_items.clear()
        self._conflict_ids.clear()

        # Header dates
        for col in range(7):
            label = (start + timedelta(days=col)).strftime("%a %d")
            self.table.setHorizontalHeaderItem(col, QTableWidgetItem(label))

        # Fill cells and mark conflicts
        for d, items in items_by_day.items():
            col = (d - start).days
            ranges = [TimeRange(i.start, i.end) for i in items]
            conflicts = find_conflicts(ranges)  # list[tuple[int, int]]
            conflicted = {idx for a, b in conflicts for idx in (a, b)}

            for idx, item in enumerate(items):
                row = item.start.hour
                cell = self.table.item(row, col)
                text = item.title
                if cell:
                    cell.setText(cell.text() + " / " + text)
                else:
                    cell = QTableWidgetItem(text)

                if idx in conflicted:
                    cell.setBackground(QColor("red"))
                    cell.setToolTip("Overlaps with another item")
                    self._conflict_ids.add(item.id)

                self.table.setItem(row, col, cell)
                self._cell_items[(row, col)] = item

        # Month badges (counts per day)
        month_start = date(self.current_day.year, self.current_day.month, 1)
        next_month = month_start.replace(day=28) + timedelta(days=4)  # always flips to next month
        month_end = next_month - timedelta(days=next_month.day)
        counts: Dict[date, int] = {}
        monthly = self.model.fetch_range(month_start, month_end)
        for d, items in monthly.items():
            counts[d] = len(items)
        self.month.set_badges(counts)
        self.month.setSelectedDate(self.current_day)

    # ----- selection & dialogs -----
    def on_cell_clicked(self, row: int, col: int) -> None:
        self.selected_item = self._cell_items.get((row, col))

    def open_quick_add(self) -> None:
        from .quick_add_dialog import QuickAddDialog  # local import to keep init light
        dlg = QuickAddDialog(self.engine, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self.refresh()

    def edit_selected(self) -> None:
        if not self.selected_item:
            return
        from .quick_add_dialog import QuickAddDialog
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

    # ----- keyboard -----
    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        key = event.key()
        mods = event.modifiers()

        if key == Qt.Key.Key_N:
            self.open_quick_add()
            return
        if key == Qt.Key.Key_Delete and self.selected_item:
            if self.selected_item.table == "events" and self.selected_item.source == "app":
                self.model.delete_item(self.selected_item)
                self.refresh()
            return
        if key == Qt.Key.Key_E and self.selected_item:
            self.edit_selected()
            return
        if key == Qt.Key.Key_K and (mods & Qt.KeyboardModifier.ControlModifier or mods & Qt.KeyboardModifier.MetaModifier):
            self.open_quick_add()
            return

        super().keyPressEvent(event)

    # ----- drag/resize & hover -----
    def eventFilter(self, source, event):  # type: ignore[override]
        if source is self._viewport:
            et = event.type()

            if et == QEvent.Type.MouseMove:
                pos = event.position().toPoint()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())
                item = self._cell_items.get((row, col))
                if item:
                    model = self.table.model()
                    if model is not None:
                        rect = self.table.visualRect(model.index(row, col))
                        global_pos = self._viewport.mapToGlobal(rect.topRight())
                        self.hover_card.show_item(item, conflict=item.id in self._conflict_ids, pos=global_pos)
                    else:
                        self.hover_card.hide_card()
                else:
                    self.hover_card.hide_card()
                return False

            if et == QEvent.Type.Leave:
                self.hover_card.hide_card()
                return False

            if et == QEvent.Type.MouseButtonDblClick:
                pos = event.position().toPoint()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())
                if (row, col) not in self._cell_items and row >= 0 and col >= 0:
                    day = self.week_start() + timedelta(days=col)
                    start_dt = datetime.combine(day, time(row))
                    model = self.table.model()
                    if model is not None:
                        rect = self.table.visualRect(model.index(row, col))
                        self.quick_inline.start(rect, start_dt)
                        return True

            if et == QEvent.Type.MouseButtonPress:
                pos = event.position().toPoint()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())
                item = self._cell_items.get((row, col))
                if not item:
                    return False

                self.selected_item = item
                self._drag_item = item
                self._drag_start = (row, col)

                model = self.table.model()
                if model is not None:
                    rect = self.table.visualRect(model.index(row, col))
                    margin = 5
                    if abs(pos.y() - rect.top()) <= margin:
                        self._resize_edge = "start"
                    elif abs(pos.y() - rect.bottom()) <= margin:
                        self._resize_edge = "end"
                    else:
                        self._resize_edge = None
                else:
                    self._resize_edge = None

                return True

            if et == QEvent.Type.MouseButtonRelease and self._drag_item:
                pos = event.position().toPoint()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())

                if row < 0 or col < 0 or self._drag_start is None:
                    self._drag_item = None
                    self._resize_edge = None
                    return False

                d_row = row - self._drag_start[0]
                d_col = col - self._drag_start[1]

                start = self._drag_item.start
                end = self._drag_item.end

                if self._resize_edge == "start":
                    new_start = start + timedelta(days=d_col, hours=d_row)
                    new_end = end
                elif self._resize_edge == "end":
                    new_start = start
                    new_end = end + timedelta(days=d_col, hours=d_row)
                else:
                    new_start = start + timedelta(days=d_col, hours=d_row)
                    new_end = end + timedelta(days=d_col, hours=d_row)

                self.model.update_item_time(self._drag_item, new_start, new_end)
                self._drag_item = None
                self._resize_edge = None
                self.refresh()
                return True

        return super().eventFilter(source, event)
