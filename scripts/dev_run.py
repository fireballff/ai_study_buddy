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

    # -----------------------------
    # Set app icon (works in EXE and dev mode)
    from pathlib import Path
    from PyQt6.QtGui import QIcon

    exe_dir = Path(sys.argv[0]).resolve().parent
    icon_path = exe_dir / "app.ico"
    if not icon_path.exists():
        icon_path = Path(__file__).resolve().parents[1] / "packaging" / "app.ico"

    app.setWindowIcon(QIcon(str(icon_path)))
    # -----------------------------

    window = MainWindow(settings=settings, engine=engine)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    # Ensure the project root is in sys.path
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    main()
