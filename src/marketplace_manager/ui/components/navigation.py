"""Navigation sidebar used by the main window."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QLabel, QPushButton, QVBoxLayout, QWidget


class NavigationSidebar(QWidget):
    page_requested = Signal(int)

    def __init__(self, page_names: tuple[str, ...], version: str) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 18)
        brand = QLabel("Marketplace Manager")
        brand.setObjectName("brandName")
        tag = QLabel(f"DESKTOP APP • v{version}")
        tag.setObjectName("brandTagline")
        layout.addWidget(brand); layout.addWidget(tag); layout.addSpacing(24)
        group = QButtonGroup(self); group.setExclusive(True)
        for index, name in enumerate(page_names):
            button = QPushButton(name); button.setObjectName("navigationButton")
            button.setCheckable(True); button.setMinimumHeight(42)
            button.clicked.connect(lambda checked=False, page=index: self.page_requested.emit(page))
            group.addButton(button, index); layout.addWidget(button)
            if index == 0: button.setChecked(True)
        layout.addStretch()
