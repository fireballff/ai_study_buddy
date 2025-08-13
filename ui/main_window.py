from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QVBoxLayout

from project.settings import Settings, load_settings
from project.db import get_engine, ensure_db
from integrations.auth_supabase import SupabaseAuth

from ui.components.sidebar import Sidebar
from ui.pages.home import HomePage
from ui.calendar.week_view import WeekView  # <- fixed path
from ui.pages.tasks import TasksPage
from ui.pages.planner import PlannerPage
from ui.pages.settings_page import SettingsPage
from ui.pages.adhd_mode import ADHDModePage
from ui.theme_manager import build_stylesheet


class MainWindow(QMainWindow):
    """Main application window with a sidebar and stacked pages. Handles theme switching and navigation."""

    def __init__(self, settings: Settings | None = None, engine=None, parent=None):
        super().__init__(parent)
        self.settings = settings or load_settings()
        self.setWindowTitle(self.settings.app_name)
        self.resize(1100, 740)

        # Database engine
        self.engine = engine or get_engine(self.settings.sqlite_path)
        ensure_db(self.engine)

        # Supabase auth (stubbed in sample mode)
        self.auth = SupabaseAuth(
            self.settings.supabase_url,
            self.settings.supabase_anon_key,
            self.settings.sample_mode,
        )

        container = QWidget(self)
        root = QHBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar for navigation
        self.sidebar = Sidebar(self)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar.navigate.connect(self.on_navigate)

        # Stacked widget to hold pages
        self.stack = QStackedWidget(self)

        # Instantiate pages with dependencies
        self.pages = {
            "home": HomePage(self),
            "calendar": WeekView(self.engine, self),
            "tasks": TasksPage(self.engine, self),
            "planner": PlannerPage(self.engine, self),
            "settings": SettingsPage(self.settings, self.auth, self),
            "adhd": ADHDModePage(self.engine, self),
        }
        for key in ("home", "calendar", "tasks", "planner", "settings", "adhd"):
            self.stack.addWidget(self.pages[key])

        root.addWidget(self.sidebar)

        if self.settings.enable_adhd_mode:
            # Focus/ADHD layout replaces the standard stack
            from ui.adhd.timer_widget import TimerWidget
            from ui.adhd.focus_timeline import FocusTimeline
            from ui.adhd.one_thing_now import OneThingNow

            self.sidebar.hide()
            panel = QWidget(self)
            panel_layout = QVBoxLayout(panel)
            self.timer_widget = TimerWidget(self.settings, self)
            self.one_thing_now = OneThingNow(self)
            self.focus_timeline = FocusTimeline(self)
            panel_layout.addWidget(self.timer_widget)
            panel_layout.addWidget(self.one_thing_now)
            panel_layout.addWidget(self.focus_timeline)
            root.addWidget(panel, 1)
        else:
            root.addWidget(self.stack, 1)

        self.setCentralWidget(container)

        # Apply initial theme and connect dark mode toggle
        self.apply_theme(self.settings.enable_dark_mode)
        self.pages["settings"].toggle_dark_mode.connect(self.apply_theme)
        self.pages["settings"].user_signed_out.connect(self.handle_sign_out)

        # Show home page by default
        self.on_navigate("home")

    def on_navigate(self, key: str) -> None:
        """Switch to the page corresponding to the navigation key."""
        page = self.pages.get(key, self.pages["home"])
        if key == "adhd":
            # Refresh task list in focus mode each time it's opened
            self.pages["adhd"].refresh_tasks()
        self.stack.setCurrentWidget(page)

    def apply_theme(self, dark: bool) -> None:
        """Apply the dark or light theme across the entire window."""
        self.settings.enable_dark_mode = bool(dark)
        self.setStyleSheet(build_stylesheet(dark))
        # Keep settings page checkbox in sync
        settings_page = self.pages.get("settings")
        if settings_page:
            settings_page.chk_dark.blockSignals(True)
            settings_page.chk_dark.setChecked(bool(dark))
            settings_page.chk_dark.blockSignals(False)

    def handle_sign_out(self) -> None:
        """Stub for handling sign‑out events."""
        # In a real implementation, this could clear caches and return to login.
        pass
