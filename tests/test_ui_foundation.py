"""UI foundation regression tests."""

from PySide6.QtWidgets import QApplication

from marketplace_manager.ui.main_window import MainWindow
from marketplace_manager.ui.pages.listings_page import ListingsPage
from marketplace_manager.ui.pages.settings_page import SettingsPage


def test_main_window_uses_real_phase_2_pages() -> None:
    """The remaining placeholder sections are replaced with real UI pages."""
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.pages.count() == len(window.PAGE_NAMES)
    assert isinstance(window.pages.widget(2), ListingsPage)
    assert isinstance(window.pages.widget(6), SettingsPage)

    window.close()
    app.processEvents()
