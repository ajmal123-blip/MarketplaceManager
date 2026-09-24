"""UI for safe local internal-task scheduling."""

from datetime import datetime

from PySide6.QtCore import QDateTime, QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
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

from marketplace_manager.database.service import initialize_database
from marketplace_manager.scheduler.service import TASK_TYPES, SchedulerService
from marketplace_manager.ui.pages.common import page_header


class SchedulerPage(QWidget):
    """Manage local scheduled tasks without blocking the Qt UI thread."""

    def __init__(self) -> None:
        super().__init__()
        self.service = SchedulerService(initialize_database())
        self.service.start_background()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(16)
        page_header(layout, "Scheduler", "Schedule safe internal application tasks. Nothing is published automatically.")

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search task name or type...")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Running", "Completed", "Failed", "Disabled"])
        add = QPushButton("Add task")
        edit = QPushButton("Edit task")
        toggle = QPushButton("Enable / Disable")
        delete = QPushButton("Delete")
        run = QPushButton("Run due tasks")
        history = QPushButton("History")
        refresh = QPushButton("Refresh")
        controls.addWidget(self.search, 1)
        controls.addWidget(self.status_filter)
        for button in (add, edit, toggle, delete, run, history, refresh):
            controls.addWidget(button)
        layout.addLayout(controls)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Task name", "Task type", "Scheduled date", "Scheduled time", "Status",
             "Enabled", "Created", "Last run", "Next run"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        add.clicked.connect(self.create)
        edit.clicked.connect(self.edit)
        toggle.clicked.connect(self.toggle)
        delete.clicked.connect(self.delete)
        run.clicked.connect(self.run_due)
        history.clicked.connect(self.show_history)
        refresh.clicked.connect(self.refresh)
        self.search.textChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start()
        self.refresh()

    def refresh(self) -> None:
        status = self.status_filter.currentText().lower()
        rows = self.service.list_tasks(self.search.text(), "All" if status == "all" else status)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            display_status = "Disabled" if not row["enabled"] else str(row["status"]).title()
            values = (
                str(row["id"]), row["task_name"], row["task_type"], self._date(row["scheduled_at"]),
                self._time(row["scheduled_at"]), display_status, "Yes" if row["enabled"] else "No",
                self._date_time(row["created_at"]), self._date_time(row["last_run"]), self._date_time(row["next_run"]),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 5:
                    item.setForeground(self._status_color(display_status))
                self.table.setItem(row_index, column, item)

    @staticmethod
    def _date(value: str | None) -> str:
        return value[:10] if value else ""

    @staticmethod
    def _time(value: str | None) -> str:
        return value[11:16] if value else ""

    @staticmethod
    def _date_time(value: str | None) -> str:
        return value.replace("T", " ")[:19] if value else ""

    @staticmethod
    def _status_color(status: str) -> QColor:
        return {
            "Completed": QColor("#2e8b57"), "Failed": QColor("#c0392b"),
            "Running": QColor("#3766c9"), "Disabled": QColor("#667085"),
        }.get(status, QColor("#b7791f"))

    def selected_id(self) -> int | None:
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return int(item.text()) if item else None

    def _task_dialog(self, existing=None) -> tuple[str, str, datetime] | None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit scheduled task" if existing else "Add scheduled task")
        dialog.setMinimumWidth(420)
        form = QFormLayout(dialog)
        name = QLineEdit(existing["task_name"] if existing else "")
        name.setPlaceholderText("e.g. Prepare evening draft")
        kind = QComboBox()
        kind.addItems(TASK_TYPES)
        if existing:
            kind.setCurrentText(existing["task_type"])
        when = QDateTimeEdit(QDateTime.currentDateTime().addSecs(60))
        when.setCalendarPopup(True)
        when.setDisplayFormat("yyyy-MM-dd HH:mm")
        if existing:
            when.setDateTime(QDateTime.fromString(existing["scheduled_at"], QtDateFormat.ISO))
        form.addRow("Task name", name)
        form.addRow("Task type", kind)
        form.addRow("Scheduled date/time", when)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return name.text().strip(), kind.currentText(), when.dateTime().toPython()

    def create(self) -> None:
        values = self._task_dialog()
        if values is None:
            return
        try:
            self.service.create(*values)
            self.refresh()
        except ValueError as error:
            QMessageBox.warning(self, "Invalid scheduled task", str(error))

    def edit(self) -> None:
        task_id = self.selected_id()
        if task_id is None:
            QMessageBox.information(self, "Select a task", "Select a task to edit.")
            return
        existing = self.service.get(task_id)
        values = self._task_dialog(existing)
        if values is None:
            return
        try:
            self.service.edit(task_id, *values)
            self.refresh()
        except ValueError as error:
            QMessageBox.warning(self, "Invalid scheduled task", str(error))

    def toggle(self) -> None:
        task_id = self.selected_id()
        if task_id is not None:
            row = self.service.get(task_id)
            if row is not None:
                self.service.set_enabled(task_id, not bool(row["enabled"]))
                self.refresh()

    def run_due(self) -> None:
        self.service.run_due()
        self.refresh()
        QMessageBox.information(self, "Scheduler", "Due internal tasks were processed safely.")

    def delete(self) -> None:
        task_id = self.selected_id()
        if task_id is not None and QMessageBox.question(
            self, "Delete task", "Delete the selected scheduled task?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            self.service.delete(task_id)
            self.refresh()

    def show_history(self) -> None:
        task_id = self.selected_id()
        if task_id is None:
            return
        entries = self.service.history(task_id)
        text = "\n".join(
            f"{row['executed_at']} — {row['status']}: {row['message']}" for row in entries
        ) or "No executions yet."
        QMessageBox.information(self, "Execution history", text)

    def shutdown(self) -> None:
        self._refresh_timer.stop()
        self.service.shutdown()


# ISO format is accepted by QDateTime.fromString without exposing configuration values.
QtDateFormat = Qt.DateFormat.ISODate
