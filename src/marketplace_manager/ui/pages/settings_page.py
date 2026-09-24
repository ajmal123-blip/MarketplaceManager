"""Application settings and workspace preferences page."""

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from marketplace_manager.core.config import AppSettings, load_app_settings, save_app_settings
from marketplace_manager.ui.pages.common import page_header


class SettingsPage(QWidget):
    """Collect basic app preferences and workspace defaults."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = load_app_settings()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(20)

        page_header(layout, "Settings", "Configure the workspace defaults for your local workflow.")

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.workspace_name = QLineEdit(self.settings.workspace_name)
        self.default_currency = QLineEdit(self.settings.default_currency)
        self.default_location = QLineEdit(self.settings.default_location)
        self.default_status = QLineEdit(self.settings.default_product_status)

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
        self.save_button = QPushButton("Save settings")
        self.reset_button = QPushButton("Reset")
        actions.addWidget(self.reset_button)
        actions.addWidget(self.save_button)
        layout.addLayout(actions)

        self.status_label = QLabel("No changes saved yet.")
        self.status_label.setObjectName("pageSubtitle")
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.reset_button.clicked.connect(self.reset_settings)
        self.save_button.clicked.connect(self.save_settings)

    def _settings_from_form(self) -> AppSettings:
        return AppSettings(
            workspace_name=self.workspace_name.text().strip() or self.settings.workspace_name,
            default_currency=self.default_currency.text().strip() or self.settings.default_currency,
            default_location=self.default_location.text().strip() or self.settings.default_location,
            default_product_status=self.default_status.text().strip() or self.settings.default_product_status,
            ai_provider=self.settings.ai_provider,
        )

    def save_settings(self) -> None:
        """Persist the current settings to the local application settings file."""
        self.settings = self._settings_from_form()
        save_app_settings(self.settings)
        self.status_label.setText(f"Saved local settings for {self.settings.workspace_name}.")

    def reset_settings(self) -> None:
        """Reset the form to defaults and save them locally."""
        self.settings = load_app_settings()
        self.workspace_name.setText(self.settings.workspace_name)
        self.default_currency.setText(self.settings.default_currency)
        self.default_location.setText(self.settings.default_location)
        self.default_status.setText(self.settings.default_product_status)
        save_app_settings(self.settings)
        self.status_label.setText("Settings reset to the default workspace values.")
