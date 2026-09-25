"""Complete application settings and workspace preferences page."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from marketplace_manager.core.config import (
    DATA_DIR,
    LOG_DIR,
    SETTINGS_PATH,
    THEME_NAME,
    VALID_LOG_LEVELS,
    VALID_STARTUP_BEHAVIORS,
    AppSettings,
    load_app_settings,
    save_app_settings,
    validate_app_settings,
)
from marketplace_manager.core.logging_config import configure_logging
from marketplace_manager.ui.pages.common import page_header


class SettingsPage(QWidget):
    """Persist safe application preferences without storing secret values."""

    connections_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.settings = load_app_settings()
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(14)
        page_header(root, "Settings", "Configure workspace, appearance, AI, storage, notifications, and safe logging preferences.")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(14)
        layout.addWidget(self._general_section())
        layout.addWidget(self._appearance_section())
        layout.addWidget(self._ai_section())
        layout.addWidget(self._storage_section())
        layout.addWidget(self._notifications_section())
        layout.addWidget(self._logging_section())
        layout.addWidget(self._connections_section())
        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        self.reset_button = QPushButton("Reset")
        self.apply_button = QPushButton("Apply")
        self.save_button = QPushButton("Save settings")
        actions.addWidget(self.reset_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.save_button)
        root.addLayout(actions)
        self.status_label = QLabel("No changes saved yet.")
        self.status_label.setObjectName("pageSubtitle")
        root.addWidget(self.status_label)
        self.reset_button.clicked.connect(self.reset_settings)
        self.apply_button.clicked.connect(self.apply_settings)
        self.save_button.clicked.connect(self.save_settings)
        self._populate(self.settings)

    @staticmethod
    def _section(title: str) -> tuple[QGroupBox, QFormLayout]:
        box = QGroupBox(title)
        form = QFormLayout(box)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        return box, form

    def _general_section(self) -> QWidget:
        box, form = self._section("General")
        self.application_name = QLineEdit()
        self.workspace_name = self.application_name  # Backward-compatible page attribute.
        self.default_currency = QLineEdit()
        self.default_location = QLineEdit()
        self.default_status = QLineEdit()
        self.startup_behavior = QComboBox()
        self.startup_behavior.addItems(VALID_STARTUP_BEHAVIORS)
        self.confirm_before_delete = QCheckBox("Confirm destructive actions")
        form.addRow("Application name", self.application_name)
        form.addRow("Default currency", self.default_currency)
        form.addRow("Default location", self.default_location)
        form.addRow("Default product status", self.default_status)
        form.addRow("Startup behavior", self.startup_behavior)
        form.addRow("Confirmation preferences", self.confirm_before_delete)
        self._general_box = box
        return box

    def _appearance_section(self) -> QWidget:
        box, form = self._section("Appearance")
        self.theme = QComboBox()
        self.theme.addItem(THEME_NAME)
        self.compact_ui = QCheckBox("Use compact controls")
        form.addRow("Theme", self.theme)
        form.addRow("UI preferences", self.compact_ui)
        return box

    def _ai_section(self) -> QWidget:
        box, form = self._section("AI Configuration")
        self.ai_provider = QComboBox()
        self.ai_provider.addItems(["mock", "unavailable"])
        self.ai_status = QLabel("Local mock provider is available; no network calls are required.")
        self.ai_status.setObjectName("placeholderText")
        self.ai_secret_env_var = QLineEdit()
        self.ai_secret_env_var.setPlaceholderText("Environment variable name only")
        self.ai_secret_value = QLineEdit()
        self.ai_secret_value.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_secret_value.setPlaceholderText("Never stored or displayed")
        form.addRow("Provider", self.ai_provider)
        form.addRow("Configuration status", self.ai_status)
        form.addRow("Secret environment variable", self.ai_secret_env_var)
        form.addRow("API key / secret", self.ai_secret_value)
        self._ai_box = box
        return box

    def _storage_section(self) -> QWidget:
        box, form = self._section("Storage")
        self.data_directory = QLineEdit(str(DATA_DIR))
        self.log_directory = QLineEdit(str(LOG_DIR))
        self.configuration_file = QLineEdit(str(SETTINGS_PATH))
        for field in (self.data_directory, self.log_directory, self.configuration_file):
            field.setReadOnly(True)
        form.addRow("Data directory", self.data_directory)
        form.addRow("Log directory", self.log_directory)
        form.addRow("Configuration file", self.configuration_file)
        return box

    def _notifications_section(self) -> QWidget:
        box, form = self._section("Notifications")
        self.notifications_enabled = QCheckBox("Enable notifications")
        self.notify_on_task_failure = QCheckBox("Notify when a local task fails")
        form.addRow("Notifications", self.notifications_enabled)
        form.addRow("Preferences", self.notify_on_task_failure)
        return box

    def _logging_section(self) -> QWidget:
        box, form = self._section("Logging")
        self.log_level = QComboBox()
        self.log_level.addItems(VALID_LOG_LEVELS)
        self.log_retention_days = QSpinBox()
        self.log_retention_days.setRange(0, 3650)
        self.log_retention_days.setSuffix(" days")
        self.logging_note = QLabel("Logs use the existing application logger and redact secret-shaped values in the Activity Logs view.")
        self.logging_note.setObjectName("placeholderText")
        self.logging_note.setWordWrap(True)
        form.addRow("Log level", self.log_level)
        form.addRow("Log retention", self.log_retention_days)
        form.addRow("Safe logging", self.logging_note)
        return box

    def _connections_section(self) -> QWidget:
        box, form = self._section("Connections")
        self.show_connection_activity = QCheckBox("Show connection activity in local logs")
        open_button = QPushButton("Open Connections")
        open_button.clicked.connect(self.connections_requested.emit)
        form.addRow("Connection preferences", self.show_connection_activity)
        form.addRow("Management", open_button)
        return box

    def _settings_from_form(self) -> AppSettings:
        return AppSettings(
            workspace_name=self.application_name.text().strip(),
            default_currency=self.default_currency.text().strip(),
            default_location=self.default_location.text().strip(),
            default_product_status=self.default_status.text().strip(),
            ai_provider=self.ai_provider.currentText(),
            startup_behavior=self.startup_behavior.currentText(),
            confirm_before_delete=self.confirm_before_delete.isChecked(),
            theme=self.theme.currentText(),
            compact_ui=self.compact_ui.isChecked(),
            ai_secret_env_var=self.ai_secret_env_var.text().strip(),
            notifications_enabled=self.notifications_enabled.isChecked(),
            notify_on_task_failure=self.notify_on_task_failure.isChecked(),
            log_level=self.log_level.currentText(),
            log_retention_days=self.log_retention_days.value(),
            show_connection_activity=self.show_connection_activity.isChecked(),
        )

    def _populate(self, settings: AppSettings) -> None:
        self.application_name.setText(settings.workspace_name)
        self.default_currency.setText(settings.default_currency)
        self.default_location.setText(settings.default_location)
        self.default_status.setText(settings.default_product_status)
        self.startup_behavior.setCurrentText(settings.startup_behavior)
        self.confirm_before_delete.setChecked(settings.confirm_before_delete)
        self.theme.setCurrentText(settings.theme)
        self.compact_ui.setChecked(settings.compact_ui)
        self.ai_provider.setCurrentText(settings.ai_provider if settings.ai_provider in {"mock", "unavailable"} else "unavailable")
        self.ai_secret_env_var.setText(settings.ai_secret_env_var)
        self.ai_secret_value.clear()
        self.notifications_enabled.setChecked(settings.notifications_enabled)
        self.notify_on_task_failure.setChecked(settings.notify_on_task_failure)
        self.log_level.setCurrentText(settings.log_level if settings.log_level in VALID_LOG_LEVELS else "INFO")
        self.log_retention_days.setValue(max(0, min(3650, settings.log_retention_days)))
        self.show_connection_activity.setChecked(settings.show_connection_activity)

    def apply_settings(self) -> bool:
        candidate = self._settings_from_form()
        errors = validate_app_settings(candidate)
        if errors:
            self.status_label.setText("Settings need attention: " + " ".join(errors))
            QMessageBox.warning(self, "Invalid settings", "\n".join(errors))
            return False
        try:
            save_app_settings(candidate)
            self.settings = candidate
            self.ai_secret_value.clear()
            configure_logging()
            self.status_label.setText("Settings applied safely.")
            return True
        except (OSError, ValueError) as error:
            self.status_label.setText("Settings could not be saved.")
            QMessageBox.critical(self, "Settings error", str(error))
            return False

    def save_settings(self) -> bool:
        return self.apply_settings()

    def reset_settings(self) -> None:
        self._populate(AppSettings())
        self.status_label.setText("Form reset to safe defaults. Apply or Save to persist changes.")
