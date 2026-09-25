"""Main window and responsive page navigation."""
import logging
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QStatusBar, QWidget
from marketplace_manager import __version__
from marketplace_manager.ui.components.navigation import NavigationSidebar
from marketplace_manager.ui.pages.common import PlaceholderPage
from marketplace_manager.ui.pages.dashboard import DashboardPage
from marketplace_manager.ui.pages.products_page import ProductsPage
from marketplace_manager.ui.pages.listings_page import ListingsPage
from marketplace_manager.ui.pages.images_page import ImagesPage
from marketplace_manager.ui.pages.ai_writer_page import AIWriterPage
from marketplace_manager.ui.pages.scheduler_page import SchedulerPage
from marketplace_manager.ui.pages.settings_page import SettingsPage
from marketplace_manager.ui.pages.imports_page import ImportsPage
from marketplace_manager.ui.pages.connections_page import ConnectionsPage
from marketplace_manager.ui.pages.activity_logs_page import ActivityLogsPage


class MainWindow(QMainWindow):
    """Professional application shell for current and future modules."""
    PAGE_NAMES = ("Dashboard", "Products", "Listings", "Images", "AI Writer", "Scheduler", "Settings", "CSV / Excel", "Connections", "Activity Logs")

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"FBauto Bot 33 {__version__}")
        self.setMinimumSize(QSize(900, 600))
        self.resize(1280, 800)
        self._build_interface()
        logging.getLogger(__name__).info("Main window created")

    def _build_interface(self) -> None:
        root = QWidget(); root.setObjectName("appRoot")
        layout = QHBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        self.sidebar = NavigationSidebar(self.PAGE_NAMES, __version__)
        self.sidebar.page_requested.connect(self.show_page)
        self.pages = QStackedWidget()
        self.pages.addWidget(DashboardPage())
        self.pages.addWidget(ProductsPage())
        self.pages.addWidget(ListingsPage())
        self.pages.addWidget(ImagesPage())
        self.pages.addWidget(AIWriterPage())
        self.pages.addWidget(SchedulerPage())
        settings_page = SettingsPage()
        settings_page.connections_requested.connect(lambda: self.show_page(self.PAGE_NAMES.index("Connections")))
        self.pages.addWidget(settings_page)
        self.pages.addWidget(ImportsPage())
        self.pages.addWidget(ConnectionsPage())
        self.pages.addWidget(ActivityLogsPage())
        layout.addWidget(self.sidebar); layout.addWidget(self.pages, 1); self.setCentralWidget(root)
        status = QStatusBar(); status.showMessage("Ready")
        version = QLabel(f"Version {__version__}"); status.addPermanentWidget(version); self.setStatusBar(status)
        self._apply_style()

    def show_page(self, index: int) -> None:
        try:
            if not 0 <= index < self.pages.count(): raise IndexError(index)
            self.pages.setCurrentIndex(index); self.statusBar().showMessage(f"{self.PAGE_NAMES[index]} selected")
        except (IndexError, RuntimeError):
            logging.getLogger(__name__).exception("Unable to change page")
            self.statusBar().showMessage("Unable to open the requested page")

    def closeEvent(self, event) -> None:
        """Shut down page-owned workers before closing the application."""
        for index in range(self.pages.count()):
            page = self.pages.widget(index)
            shutdown = getattr(page, "shutdown", None)
            if callable(shutdown):
                shutdown()
        super().closeEvent(event)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, #appRoot { background: #f7f8fc; color: #172033; }
            #sidebar { background: #172033; min-width: 235px; max-width: 235px; }
            #brandName { color: white; font-size: 19px; font-weight: 700; }
            #brandTagline { color: #a8b5ca; font-size: 11px; }
            QPushButton#navigationButton { border: 0; border-radius: 7px; color: #cbd5e1; font-size: 14px; padding: 11px 14px; text-align: left; }
            QPushButton#navigationButton:hover { background: #24334d; color: white; }
            QPushButton#navigationButton:checked { background: #3766c9; color: white; font-weight: 600; }
            #pageTitle { color: #172033; font-size: 28px; font-weight: 700; }
            #pageSubtitle, #placeholderText, #cardLabel { color: #667085; font-size: 14px; }
            #card { background: white; border: 1px solid #e5e9f2; border-radius: 10px; }
            #cardValue { color: #172033; font-size: 25px; font-weight: 700; }
            #placeholderIcon { color: #3766c9; font-size: 30px; font-weight: 700; }
            QStatusBar { background: white; border-top: 1px solid #e5e9f2; color: #667085; }
        """)
