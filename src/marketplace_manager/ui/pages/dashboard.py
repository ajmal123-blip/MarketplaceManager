"""Dashboard page."""
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.ui.pages.common import page_header


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._connection = initialize_database()
        self._repository = ProductRepository(self._connection)
        layout = QVBoxLayout(self); layout.setContentsMargins(36, 32, 36, 32); layout.setSpacing(24)
        page_header(layout, "Dashboard", "Your Marketplace Manager workspace at a glance.")
        grid = QGridLayout(); grid.setSpacing(16)
        counts = self._repository.counts_by_status()
        cards = (
            ("Products", counts["total"]),
            ("Active", counts["active"]),
            ("Draft", counts["draft"]),
            ("Archived", counts["archived"]),
        )
        for index, (label, value) in enumerate(cards):
            card = QFrame(); card.setObjectName("card")
            card_layout = QVBoxLayout(card); card_layout.setContentsMargins(20, 18, 20, 18)
            value_label = QLabel(str(value)); value_label.setObjectName("cardValue")
            name = QLabel(label); name.setObjectName("cardLabel")
            card_layout.addWidget(value_label); card_layout.addWidget(name)
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid); layout.addStretch()
