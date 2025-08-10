from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication
from project.settings import load_settings
from project.logging import configure_logging
from project.db import get_engine, ensure_db
from ui.main_window import MainWindow
from utils.error_handler import install_global_exception_hook


def main():
    settings = load_settings()
    logger = configure_logging(settings.app_log_level)
    engine = get_engine(settings.sqlite_path)
    ensure_db(engine)
    install_global_exception_hook(logger)
    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    window = MainWindow(settings=settings, engine=engine)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()