"""Reusable page elements."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


def page_header(layout: QVBoxLayout, title_text: str, subtitle_text: str) -> None:
    title = QLabel(title_text); title.setObjectName("pageTitle")
    subtitle = QLabel(subtitle_text); subtitle.setObjectName("pageSubtitle")
    layout.addWidget(title); layout.addWidget(subtitle)


class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(36, 32, 36, 32); layout.setSpacing(12)
        page_header(layout, title, description); layout.addStretch()
        card = QFrame(); card.setObjectName("card")
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(32, 32, 32, 32)
        icon = QLabel("+"); icon.setObjectName("placeholderIcon"); icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text = QLabel("This workspace is ready for a future project phase."); text.setObjectName("placeholderText")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon); card_layout.addWidget(text)
        layout.addWidget(card); layout.addStretch()
