"""Professional, safe local connection management UI."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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

from marketplace_manager.connections.service import (
    CONNECTION_TYPES,
    ConnectionService,
    mask_sensitive,
)
from marketplace_manager.database.service import initialize_database
from marketplace_manager.ui.pages.common import page_header


class ConnectionDialog(QDialog):
    """Collect non-secret connection metadata; transient secret input is never saved."""

    def __init__(self, parent=None, existing=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit connection" if existing else "New connection")
        self.setMinimumWidth(440)
        form = QFormLayout(self)
        self.name = QLineEdit(existing.name if existing else "")
        self.connection_type = QComboBox()
        self.connection_type.addItems(CONNECTION_TYPES)
        if existing:
            self.connection_type.setCurrentText(existing.connection_type)
        self.endpoint = QLineEdit(existing.endpoint if existing else "")
        self.endpoint.setPlaceholderText("Optional local/provider endpoint")
        self.secret_ref = QLineEdit(existing.secret_ref if existing else "")
        self.secret_ref.setPlaceholderText("e.g. MARKETPLACE_API_KEY")
        self.secret_value = QLineEdit()
        self.secret_value.setEchoMode(QLineEdit.EchoMode.Password)
        self.secret_value.setPlaceholderText("Not stored; reserved for a configured provider")
        self.security_note = QLabel("Secrets are masked and never stored in the local database.")
        self.security_note.setObjectName("placeholderText")
        self.security_note.setWordWrap(True)
        form.addRow("Connection name *", self.name)
        form.addRow("Connection type *", self.connection_type)
        form.addRow("Endpoint", self.endpoint)
        form.addRow("Secret environment variable", self.secret_ref)
        form.addRow("Secret value", self.secret_value)
        form.addRow("", self.security_note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> tuple[str, str, str, str]:
        # secret_value is deliberately not returned or persisted.
        return self.name.text().strip(), self.connection_type.currentText(), self.endpoint.text().strip(), self.secret_ref.text().strip()


class ConnectionsPage(QWidget):
    """Manage local connection configurations without performing external actions."""

    def __init__(self) -> None:
        super().__init__()
        self._connection = initialize_database()
        self.service = ConnectionService(self._connection)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(16)
        page_header(layout, "Connections", "Manage safe local connection settings. No accounts or external services are accessed.")

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search connection name, type, or endpoint...")
        add = QPushButton("Add connection")
        edit = QPushButton("Edit")
        test = QPushButton("Test connection")
        toggle = QPushButton("Enable / Disable")
        delete = QPushButton("Delete")
        activity = QPushButton("Activity")
        refresh = QPushButton("Refresh")
        controls.addWidget(self.search, 1)
        for button in (add, edit, test, toggle, delete, activity, refresh):
            controls.addWidget(button)
        layout.addLayout(controls)

        self.status_label = QLabel("Ready. Connection tests use the safe local mock tester.")
        self.status_label.setObjectName("placeholderText")
        layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Type", "Status", "Enabled", "Created", "Last Tested", "Message", "Actions"]
        )
        self.table.hideColumn(0)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        add.clicked.connect(self.add_connection)
        edit.clicked.connect(self.edit_connection)
        test.clicked.connect(self.test_connection)
        toggle.clicked.connect(self.toggle_connection)
        delete.clicked.connect(self.delete_connection)
        activity.clicked.connect(self.show_activity)
        refresh.clicked.connect(self.refresh)
        self.search.textChanged.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        connections = self.service.list_connections(self.search.text())
        self.table.setRowCount(len(connections))
        for row_index, item in enumerate(connections):
            values = (
                str(item.id), item.name, item.connection_type, item.status, "Yes" if item.enabled else "No",
                self._format_datetime(item.created_at), self._format_datetime(item.last_tested), item.message,
                "Edit / Test",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 3:
                    cell.setForeground(self._status_color(item.status))
                self.table.setItem(row_index, column, cell)

    @staticmethod
    def _format_datetime(value) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""

    @staticmethod
    def _status_color(status: str) -> QColor:
        return {"Connected": QColor("#2e8b57"), "Failed": QColor("#c0392b"), "Disabled": QColor("#667085")}.get(
            status, QColor("#b7791f")
        )

    def selected_id(self) -> int | None:
        row = self.table.currentRow()
        cell = self.table.item(row, 0) if row >= 0 else None
        return int(cell.text()) if cell else None

    def add_connection(self) -> None:
        dialog = ConnectionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.create(*dialog.values())
            self.status_label.setText("Connection created safely. No secret value was stored.")
            self.refresh()
        except ValueError as error:
            QMessageBox.warning(self, "Invalid connection", str(error))

    def edit_connection(self) -> None:
        connection_id = self.selected_id()
        existing = self.service.get(connection_id) if connection_id is not None else None
        if existing is None:
            QMessageBox.information(self, "Select a connection", "Select a connection to edit.")
            return
        dialog = ConnectionDialog(self, existing)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.service.update(connection_id, *dialog.values())
            self.status_label.setText("Connection updated safely.")
            self.refresh()
        except ValueError as error:
            QMessageBox.warning(self, "Invalid connection", str(error))

    def test_connection(self) -> None:
        connection_id = self.selected_id()
        if connection_id is None:
            QMessageBox.information(self, "Select a connection", "Select a connection to test.")
            return
        result = self.service.test_connection(connection_id)
        self.status_label.setText(result.message)
        self.refresh()
        (QMessageBox.information if result.success else QMessageBox.warning)(self, "Connection test", result.message)

    def toggle_connection(self) -> None:
        connection_id = self.selected_id()
        if connection_id is None:
            return
        item = self.service.get(connection_id)
        if item is not None:
            self.service.set_enabled(connection_id, not item.enabled)
            self.status_label.setText("Connection enabled." if not item.enabled else "Connection disabled.")
            self.refresh()

    def delete_connection(self) -> None:
        connection_id = self.selected_id()
        if connection_id is None:
            return
        if QMessageBox.question(
            self, "Delete connection", "Delete this local connection configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.service.delete(connection_id)
            self.status_label.setText("Connection deleted.")
            self.refresh()

    def show_activity(self) -> None:
        connection_id = self.selected_id()
        entries = self.service.activity(connection_id)
        text = "\n".join(
            f"{entry.created_at:%Y-%m-%d %H:%M:%S} — {entry.event}: {entry.message}" for entry in entries
        ) or "No activity recorded."
        QMessageBox.information(self, "Connection activity", text)
