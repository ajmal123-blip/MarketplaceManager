"""Database-backed product management page."""
import logging
import sqlite3
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLineEdit
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.ui.product_dialog import ProductDialog
from marketplace_manager.ui.pages.common import page_header
from marketplace_manager.imports.service import export_products, import_valid_rows, read_product_file


class ProductsPage(QWidget):
    """List, filter, add, edit, and delete locally stored products."""
    def __init__(self) -> None:
        super().__init__(); self._connection = initialize_database(); self._repository = ProductRepository(self._connection)
        layout = QVBoxLayout(self); layout.setContentsMargins(36, 32, 36, 32); layout.setSpacing(16)
        page_header(layout, "Products", "Manage your local product catalog.")
        controls = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("Search title, SKU, or category...")
        self.status_filter = QComboBox(); self.status_filter.addItems(["All", "draft", "active", "archived"])
        add = QPushButton("Add Product"); edit = QPushButton("Edit"); delete = QPushButton("Delete"); refresh = QPushButton("Refresh"); importer=QPushButton("Import"); exporter=QPushButton("Export")
        controls.addWidget(self.search, 1); controls.addWidget(self.status_filter); controls.addWidget(importer); controls.addWidget(exporter); controls.addWidget(add); controls.addWidget(edit); controls.addWidget(delete); controls.addWidget(refresh); layout.addLayout(controls)
        self.table = QTableWidget(0, 6); self.table.setHorizontalHeaderLabels(["Title", "Price", "Category", "Condition", "SKU", "Status"]); self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table, 1)
        self.search.textChanged.connect(self.refresh); self.status_filter.currentTextChanged.connect(self.refresh); add.clicked.connect(self.add_product); edit.clicked.connect(self.edit_product); delete.clicked.connect(self.delete_product); refresh.clicked.connect(self.refresh); importer.clicked.connect(self.import_products); exporter.clicked.connect(self.export_products); self.table.itemDoubleClicked.connect(lambda _: self.edit_product()); self.refresh()

    def import_products(self) -> None:
        filename,_=QFileDialog.getOpenFileName(self,"Import products","","Product files (*.csv *.xlsx)")
        if not filename: return
        try: rows=read_product_file(__import__("pathlib").Path(filename))
        except (ValueError, OSError) as error: QMessageBox.warning(self,"Import error",str(error)); return
        preview=QDialog(self); preview.setWindowTitle("Import preview"); layout=QVBoxLayout(preview); table=QTableWidget(len(rows),3); table.setHorizontalHeaderLabels(["Row","Title","Validation"])
        for index,row in enumerate(rows):
            for col,value in enumerate((str(row.row_number),row.values["title"],row.error or "Ready")): table.setItem(index,col,QTableWidgetItem(value))
        layout.addWidget(table); buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(preview.accept); buttons.rejected.connect(preview.reject); layout.addWidget(buttons)
        if preview.exec():
            try: count=import_valid_rows(rows,self._repository); self.refresh(); QMessageBox.information(self,"Import complete",f"Imported {count} valid product(s). Invalid rows remain listed in the preview.")
            except sqlite3.Error as error: QMessageBox.critical(self,"Import error",str(error))

    def export_products(self) -> None:
        filename,_=QFileDialog.getSaveFileName(self,"Export products","products.csv","CSV (*.csv);;Excel (*.xlsx)")
        if not filename: return
        try: export_products(__import__("pathlib").Path(filename),self._repository.list_all()); QMessageBox.information(self,"Export complete","Products were exported successfully.")
        except (ValueError, OSError) as error: QMessageBox.critical(self,"Export error",str(error))

    def refresh(self) -> None:
        try:
            products = self._repository.list_filtered(self.search.text(), self.status_filter.currentText()); self.table.setRowCount(len(products))
            for row, product in enumerate(products):
                values = (product.title, f"{product.price:.2f}", product.category, product.condition, product.sku, product.status)
                for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(value))
                self.table.item(row, 0).setData(32, product.id)
        except sqlite3.Error:
            logging.getLogger(__name__).exception("Unable to load products"); QMessageBox.critical(self, "Database error", "Products could not be loaded. Please try again.")

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        return self.table.item(row, 0).data(32) if row >= 0 and self.table.item(row, 0) else None

    def add_product(self) -> None:
        dialog = ProductDialog(parent=self)
        if dialog.exec():
            try: self._repository.create(dialog.product()); self.refresh()
            except (sqlite3.Error, ValueError) as error: QMessageBox.critical(self, "Could not save product", str(error))

    def edit_product(self) -> None:
        product_id = self._selected_id()
        if product_id is None: QMessageBox.information(self, "Select a product", "Select a product to edit."); return
        product = self._repository.get(product_id); dialog = ProductDialog(product, self)
        if dialog.exec():
            try: self._repository.update(dialog.product()); self.refresh()
            except (sqlite3.Error, ValueError) as error: QMessageBox.critical(self, "Could not update product", str(error))

    def delete_product(self) -> None:
        product_id = self._selected_id()
        if product_id is None: QMessageBox.information(self, "Select a product", "Select a product to delete."); return
        choice = QMessageBox.question(self, "Delete product", "Delete the selected product? This cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if choice == QMessageBox.StandardButton.Yes:
            try: self._repository.delete(product_id); self.refresh()
            except sqlite3.Error: QMessageBox.critical(self, "Could not delete product", "The product could not be deleted.")
