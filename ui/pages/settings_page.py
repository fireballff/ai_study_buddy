from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton
from PyQt6.QtCore import pyqtSignal
from project.settings import Settings
from integrations.auth_supabase import SupabaseAuth


class SettingsPage(QWidget):
    """
    Settings page: toggle dark mode, sign in/out. Emits signals when dark mode toggled.
    """
    toggle_dark_mode = pyqtSignal(bool)
    user_signed_out = pyqtSignal()

    def __init__(self, settings: Settings, auth: SupabaseAuth, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.auth = auth
        layout = QVBoxLayout(self)
        title = QLabel("Settings")
        title.setObjectName("page-title")
        layout.addWidget(title)

        self.chk_dark = QCheckBox("Enable Dark Mode (override OS)")
        self.chk_dark.setChecked(settings.enable_dark_mode)
        self.chk_dark.toggled.connect(self.toggle_dark_mode.emit)
        layout.addWidget(self.chk_dark)

        self.signout_btn = QPushButton("Sign Out")
        self.signout_btn.clicked.connect(self.on_signout)
        layout.addWidget(self.signout_btn)

        layout.addStretch(1)

    def on_signout(self):
        self.auth.sign_out()
        self.user_signed_out.emit()