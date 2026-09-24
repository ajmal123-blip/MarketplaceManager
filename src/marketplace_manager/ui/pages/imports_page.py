"""CSV and Excel import/export workspace."""

import sqlite3
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from marketplace_manager.database.import_history_repository import ImportHistoryRepository
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.imports.service import (
    ImportRow,
    export_products,
    import_rows,
    read_product_file,
    validate_import_rows,
)
from marketplace_manager.ui.pages.common import page_header


class ImportsPage(QWidget):
    """Import products from CSV/XLSX and export the existing product database."""

    def __init__(self) -> None:
        super().__init__()
        self._connection = initialize_database()
        self._repository = ProductRepository(self._connection)
        self._history = ImportHistoryRepository(self._connection)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(16)
        page_header(layout, "CSV / Excel", "Safely import product data and export your local catalog.")

        actions = QHBoxLayout()
        import_csv = QPushButton("Import CSV")
        import_xlsx = QPushButton("Import XLSX")
        export_csv = QPushButton("Export CSV")
        export_xlsx = QPushButton("Export XLSX")
        refresh = QPushButton("Refresh")
        for button in (import_csv, import_xlsx, export_csv, export_xlsx, refresh):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)

        result_card = QFrame()
        result_card.setObjectName("card")
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(18, 14, 18, 14)
        result_title = QLabel("Validation and results")
        result_title.setObjectName("pageSubtitle")
        self.result_label = QLabel("Choose a CSV or XLSX file to preview its records before saving.")
        self.result_label.setObjectName("placeholderText")
        self.result_label.setWordWrap(True)
        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_label)
        layout.addWidget(result_card)

        history_title = QLabel("Import history")
        history_title.setObjectName("pageSubtitle")
        layout.addWidget(history_title)
        self.history_table = QTableWidget(0, 8)
        self.history_table.setHorizontalHeaderLabels(
            ["Date/time", "File", "Type", "Records", "Successful", "Failed", "Status", "Details"]
        )
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.history_table, 1)

        import_csv.clicked.connect(lambda: self.import_file("CSV"))
        import_xlsx.clicked.connect(lambda: self.import_file("XLSX"))
        export_csv.clicked.connect(lambda: self.export_file("CSV"))
        export_xlsx.clicked.connect(lambda: self.export_file("XLSX"))
        refresh.clicked.connect(self.refresh)
        self.refresh()

    def import_file(self, file_type: str) -> None:
        suffix = "CSV (*.csv)" if file_type == "CSV" else "Excel (*.xlsx)"
        filename, _ = QFileDialog.getOpenFileName(self, f"Import {file_type}", "", suffix)
        if not filename:
            return
        path = Path(filename)
        try:
            rows = read_product_file(path)
            validate_import_rows(rows, self._repository)
        except (ValueError, OSError) as error:
            self._history.record(path.name, file_type, 0, 0, 0, "Failed", str(error))
            self.result_label.setText(str(error))
            self.refresh()
            QMessageBox.warning(self, "Import error", str(error))
            return

        if not rows:
            message = "The file contains headers but no product records."
            self._history.record(path.name, file_type, 0, 0, 0, "Failed", message)
            self.result_label.setText(message)
            self.refresh()
            QMessageBox.warning(self, "Empty import", message)
            return

        if not self._show_preview(rows):
            return
        try:
            result = import_rows(rows, self._repository)
            status = "Completed" if result.failed_records == 0 else "Completed with errors"
            self._history.record(path.name, file_type, result.total_records, result.successful_records,
                                 result.failed_records, status)
            self.result_label.setText(
                f"{result.successful_records} record(s) imported; {result.failed_records} failed validation."
            )
            self.refresh()
            QMessageBox.information(self, "Import complete", self.result_label.text())
        except (sqlite3.Error, ValueError) as error:
            self._history.record(path.name, file_type, len(rows), 0, len(rows), "Failed", str(error))
            self.result_label.setText(str(error))
            self.refresh()
            QMessageBox.critical(self, "Import error", str(error))

    def _show_preview(self, rows: list[ImportRow]) -> bool:
        preview = QDialog(self)
        preview.setWindowTitle("Import preview")
        preview.resize(760, 420)
        layout = QVBoxLayout(preview)
        table = QTableWidget(len(rows), 4)
        table.setHorizontalHeaderLabels(["Row", "Title", "SKU", "Validation"])
        for index, row in enumerate(rows):
            values = (str(row.row_number), row.values["title"], row.values["sku"], row.error or "Ready")
            for column, value in enumerate(values):
                table.setItem(index, column, QTableWidgetItem(value))
        layout.addWidget(table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Save valid records")
        buttons.accepted.connect(preview.accept)
        buttons.rejected.connect(preview.reject)
        layout.addWidget(buttons)
        return preview.exec() == QDialog.DialogCode.Accepted

    def export_file(self, file_type: str) -> None:
        suffix = "CSV (*.csv)" if file_type == "CSV" else "Excel (*.xlsx)"
        default_name = "products.csv" if file_type == "CSV" else "products.xlsx"
        filename, _ = QFileDialog.getSaveFileName(self, f"Export {file_type}", default_name, suffix)
        if not filename:
            return
        path = Path(filename)
        try:
            export_products(path, self._repository.list_all())
            self.result_label.setText(f"Exported {len(self._repository.list_all())} product(s) to {path.name}.")
            QMessageBox.information(self, "Export complete", self.result_label.text())
        except (ValueError, OSError) as error:
            self.result_label.setText(str(error))
            QMessageBox.critical(self, "Export error", str(error))

    def refresh(self) -> None:
        history = self._history.list_recent()
        self.history_table.setRowCount(len(history))
        for row_index, item in enumerate(history):
            values = (
                item.imported_at.strftime("%Y-%m-%d %H:%M:%S"), item.file_name, item.file_type,
                str(item.records), str(item.successful_records), str(item.failed_records), item.status, item.message,
            )
            for column, value in enumerate(values):
                self.history_table.setItem(row_index, column, QTableWidgetItem(value))
