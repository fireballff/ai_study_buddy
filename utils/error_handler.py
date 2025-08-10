from __future__ import annotations
import sys
from PyQt6.QtWidgets import QMessageBox


def install_global_exception_hook(logger):
    """
    Installs a global exception hook to log uncaught exceptions and show a user-friendly dialog.
    """
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("uncaught_exception", exc_type=str(exc_type), exc=str(exc_value))
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Unexpected Error")
            msg.setText("Something went wrong.")
            msg.setInformativeText(str(exc_value))
            msg.exec()
        except Exception:
            pass
    sys.excepthook = handle_exception