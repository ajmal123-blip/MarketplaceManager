"""Dashboard page."""
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget
from marketplace_manager.ui.pages.common import page_header


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(36, 32, 36, 32); layout.setSpacing(24)
        page_header(layout, "Dashboard", "Your Marketplace Manager workspace at a glance.")
        grid = QGridLayout(); grid.setSpacing(16)
        for index, label in enumerate(("Products", "Listings", "Images", "Scheduled tasks")):
            card = QFrame(); card.setObjectName("card")
            card_layout = QVBoxLayout(card); card_layout.setContentsMargins(20, 18, 20, 18)
            value = QLabel("0"); value.setObjectName("cardValue")
            name = QLabel(label); name.setObjectName("cardLabel")
            card_layout.addWidget(value); card_layout.addWidget(name)
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid); layout.addStretch()
