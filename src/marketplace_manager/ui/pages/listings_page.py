"""Marketplace listing workspace and workflow page."""

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from marketplace_manager.ui.pages.common import page_header


class ListingsPage(QWidget):
    """Show the listings workspace with overview cards and status details."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(24)

        page_header(layout, "Listings", "Track your marketplace listing pipeline and prepare drafts.")

        overview = QGridLayout()
        overview.setSpacing(16)
        for index, (label, value) in enumerate(
            (
                ("Drafts", "0"),
                ("Ready to publish", "0"),
                ("Published this week", "0"),
                ("Needs attention", "0"),
            )
        ):
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 18, 20, 18)

            value_label = QLabel(value)
            value_label.setObjectName("cardValue")
            name = QLabel(label)
            name.setObjectName("cardLabel")

            card_layout.addWidget(value_label)
            card_layout.addWidget(name)
            overview.addWidget(card, index // 2, index % 2)

        layout.addLayout(overview)

        detail = QFrame()
        detail.setObjectName("card")
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(24, 20, 24, 20)

        detail_title = QLabel("Listing workflow")
        detail_title.setObjectName("pageSubtitle")
        detail_body = QLabel(
            "Create listing drafts in the AI Writer, review pricing and category details, and publish through your approved workflow."
        )
        detail_body.setWordWrap(True)
        detail_body.setObjectName("placeholderText")

        detail_layout.addWidget(detail_title)
        detail_layout.addWidget(detail_body)
        layout.addWidget(detail)
        layout.addStretch()
