"""Activity Logs page backed by the existing application logging file."""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from marketplace_manager.core.activity_logs import ActivityLogService, LOG_LEVELS
from marketplace_manager.ui.pages.common import page_header


class ActivityLogsPage(QWidget):
    """Browse safe, readable application log entries."""

    def __init__(self, log_path=None) -> None:
        super().__init__()
        self.service = ActivityLogService(log_path)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(16)
        page_header(layout, "Activity Logs", "Review safe application activity without exposing secrets.")

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search messages or components...")
        self.level_filter = QComboBox()
        self.level_filter.addItems(["All", *LOG_LEVELS])
        self.component_filter = QComboBox()
        self.component_filter.addItem("All")
        self.refresh_button = QPushButton("Refresh")
        self.clear_button = QPushButton("Clear Logs")
        controls.addWidget(self.search, 1)
        controls.addWidget(self.level_filter)
        controls.addWidget(self.component_filter)
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.clear_button)
        layout.addLayout(controls)

        self.status_label = QLabel("No log entries loaded.")
        self.status_label.setObjectName("placeholderText")
        layout.addWidget(self.status_label)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Level", "Component", "Message"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.search.textChanged.connect(self.refresh)
        self.level_filter.currentTextChanged.connect(self.refresh)
        self.component_filter.currentTextChanged.connect(self.refresh)
        self.refresh_button.clicked.connect(self.refresh)
        self.clear_button.clicked.connect(self.clear_logs)
        self.refresh()

    def refresh(self) -> None:
        previous_component = self.component_filter.currentText()
        components = ["All", *self.service.components()]
        self.component_filter.blockSignals(True)
        self.component_filter.clear()
        self.component_filter.addItems(components)
        self.component_filter.setCurrentText(previous_component if previous_component in components else "All")
        self.component_filter.blockSignals(False)
        entries = self.service.read(self.search.text(), self.level_filter.currentText(), self.component_filter.currentText())
        self.table.setRowCount(len(entries))
        for row_index, entry in enumerate(entries):
            values = (entry.timestamp, entry.level, entry.component, entry.message)
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 1:
                    cell.setForeground({"ERROR": QColor("#c0392b"), "WARNING": QColor("#b7791f")}.get(entry.level, QColor("#3766c9")))
                self.table.setItem(row_index, column, cell)
        self.status_label.setText(f"{len(entries)} log entr{'y' if len(entries) == 1 else 'ies'} shown.")

    def clear_logs(self) -> None:
        if QMessageBox.question(
            self,
            "Clear activity logs",
            "Clear the local application log file? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.clear()
            self.refresh()
            self.status_label.setText("Activity logs cleared.")
        except OSError:
            QMessageBox.warning(self, "Clear logs failed", "The activity log file could not be cleared.")
