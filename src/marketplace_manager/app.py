"""Application startup and lifecycle management."""

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from marketplace_manager.core.logging_config import configure_logging
from marketplace_manager.ui.main_window import MainWindow


def main() -> int:
    """Start the desktop application and return its exit code."""
    configure_logging()

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Marketplace Manager")
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as error:
        logging.getLogger(__name__).exception("Application could not start")
        QMessageBox.critical(None, "Marketplace Manager", f"The application could not start:\n{error}")
        return 1
