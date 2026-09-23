"""Dialog for adding and editing a product."""
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox, QTextEdit
from marketplace_manager.database.models import Product
from marketplace_manager.products.validation import validate_product_values


class ProductDialog(QDialog):
    """Collect validated product details from the user."""
    def __init__(self, product: Product | None = None, parent=None) -> None:
        super().__init__(parent); self._existing = product
        self.setWindowTitle("Edit Product" if product else "Add Product"); self.setMinimumWidth(440)
        layout = QFormLayout(self)
        self.title = QLineEdit(); self.description = QTextEdit(); self.description.setFixedHeight(80)
        self.price = QLineEdit(); self.category = QLineEdit(); self.condition = QLineEdit()
        self.location = QLineEdit(); self.sku = QLineEdit(); self.status = QComboBox(); self.status.addItems(["draft", "active", "archived"])
        for label, widget in (("Title *", self.title), ("Description", self.description), ("Price *", self.price), ("Category", self.category), ("Condition", self.condition), ("Location", self.location), ("SKU *", self.sku), ("Status", self.status)): layout.addRow(label, widget)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save); buttons.rejected.connect(self.reject); layout.addRow(buttons)
        if product: self._populate(product)

    def _populate(self, product: Product) -> None:
        self.title.setText(product.title); self.description.setPlainText(product.description); self.price.setText(str(product.price)); self.category.setText(product.category)
        self.condition.setText(product.condition); self.location.setText(product.location); self.sku.setText(product.sku); self.status.setCurrentText(product.status)

    def product(self) -> Product:
        price, error = validate_product_values(self.title.text(), self.price.text(), self.sku.text())
        if error or price is None: raise ValueError(error)
        return Product(self._existing.id if self._existing else None, self.title.text().strip(), self.description.toPlainText().strip(), price, self.category.text().strip(), self.condition.text().strip(), self.location.text().strip(), self.sku.text().strip(), self.status.currentText())

    def _save(self) -> None:
        try: self.product()
        except ValueError as error: QMessageBox.warning(self, "Check product details", str(error)); return
        self.accept()
