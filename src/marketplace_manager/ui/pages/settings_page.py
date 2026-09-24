"""Application settings and workspace preferences page."""

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from marketplace_manager.ui.pages.common import page_header


class SettingsPage(QWidget):
    """Collect basic app preferences and workspace defaults."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(20)

        page_header(layout, "Settings", "Configure the workspace defaults for your local workflow.")

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.workspace_name = QLineEdit("Marketplace Manager")
        self.default_currency = QLineEdit("USD")
        self.default_location = QLineEdit("Local workspace")
        self.default_status = QLineEdit("draft")

        for label, widget in (
            ("Workspace name", self.workspace_name),
            ("Default currency", self.default_currency),
            ("Default location", self.default_location),
            ("Default product status", self.default_status),
        ):
            form.addRow(label, widget)

        layout.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch()
        save = QPushButton("Save settings")
        reset = QPushButton("Reset")
        actions.addWidget(reset)
        actions.addWidget(save)
        layout.addLayout(actions)

        self.status_label = QLabel("No changes saved yet.")
        self.status_label.setObjectName("pageSubtitle")
        layout.addWidget(self.status_label)
        layout.addStretch()
