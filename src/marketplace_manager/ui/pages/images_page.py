"""Local product image management page."""
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget

from marketplace_manager.database.image_repository import ImageRepository
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.images.service import get_image_dimensions, organize_image, process_image, validate_image
from marketplace_manager.ui.pages.common import page_header


class ImagesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.connection = initialize_database()
        self.products = ProductRepository(self.connection)
        self.images = ImageRepository(self.connection)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)
        page_header(layout, "Images", "Organize local product visuals and keep them linked to the correct catalog item.")

        selector_layout = QHBoxLayout()
        self.selector = QComboBox(); self.selector.setMinimumWidth(220)
        selector_layout.addWidget(self.selector, 1)
        selector_layout.addStretch()
        refresh = QPushButton("Refresh")
        selector_layout.addWidget(refresh)
        layout.addLayout(selector_layout)

        body = QHBoxLayout(); body.setSpacing(20)
        self.list = QListWidget(); self.list.setMinimumWidth(260); self.list.setIconSize(QSize(88, 88))
        self.preview = QLabel("Select an image to preview"); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setMinimumSize(340, 260); self.preview.setStyleSheet("background: #f3f5fa; border: 1px solid #dfe6f3; border-radius: 10px;")
        body.addWidget(self.list, 1); body.addWidget(self.preview, 2)
        layout.addLayout(body, 1)

        info = QFrame(); info.setObjectName("card")
        info_layout = QVBoxLayout(info); info_layout.setContentsMargins(20, 18, 20, 18)
        self.product_name = QLabel("Product: Not selected")
        self.file_name = QLabel("File: None")
        self.dimensions = QLabel("Dimensions: N/A")
        self.info_status = QLabel("Status: Ready")
        for label in (self.product_name, self.file_name, self.dimensions, self.info_status):
            label.setWordWrap(True)
            info_layout.addWidget(label)
        layout.addWidget(info)

        buttons = QHBoxLayout(); add = QPushButton("Add Images"); remove = QPushButton("Remove"); up = QPushButton("Move Up"); down = QPushButton("Move Down"); self.resize_button = QPushButton("Resize"); self.crop_button = QPushButton("Crop"); self.rotate_button = QPushButton("Rotate"); self.optimize_button = QPushButton("Optimize")
        for button in (add, remove, up, down, self.resize_button, self.crop_button, self.rotate_button, self.optimize_button):
            buttons.addWidget(button)
        buttons.addStretch(); layout.addLayout(buttons)

        add.clicked.connect(self.add_images); remove.clicked.connect(self.remove_image); up.clicked.connect(lambda: self.move(-1)); down.clicked.connect(lambda: self.move(1)); refresh.clicked.connect(self.load_products); self.list.currentRowChanged.connect(self.show_preview); self.resize_button.clicked.connect(self.resize_selected_image); self.crop_button.clicked.connect(self.crop_selected_image); self.rotate_button.clicked.connect(self.rotate_selected_image); self.optimize_button.clicked.connect(self.optimize_selected_image); self.selector.currentIndexChanged.connect(self.refresh); self.load_products()

    def load_products(self):
        self.selector.blockSignals(True); self.selector.clear()
        for product in self.products.list_all():
            self.selector.addItem(product.title, product.id)
        self.selector.blockSignals(False)
        self.refresh()

    def _selected_image(self):
        item = self.list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _selected_product_name(self) -> str:
        product_id = self.selector.currentData()
        if product_id is None:
            return "Not selected"
        product = self.products.get(product_id)
        return product.title if product else "Unknown product"

    def refresh(self):
        self.list.clear(); product_id = self.selector.currentData()
        if not product_id:
            self.product_name.setText("Product: Not selected"); self.file_name.setText("File: None"); self.dimensions.setText("Dimensions: N/A"); self.info_status.setText("Status: Ready"); self.preview.setText("Select an image to preview"); return
        product = self.products.get(product_id)
        if product: self.product_name.setText(f"Product: {product.title}")
        for image in self.images.list_for_product(product_id):
            item = QListWidgetItem(image.original_name)
            item.setData(Qt.ItemDataRole.UserRole, image)
            self.list.addItem(item)
        self.preview.setText("Select an image to preview")

    def show_preview(self, row):
        item = self.list.item(row)
        if not item:
            self.file_name.setText("File: None"); self.dimensions.setText("Dimensions: N/A"); self.info_status.setText("Status: Ready"); self.preview.setText("Select an image to preview"); return
        image = item.data(Qt.ItemDataRole.UserRole)
        file_path = Path(image.file_path)
        self.file_name.setText(f"File: {image.original_name}")
        self.product_name.setText(f"Product: {self._selected_product_name()}")
        if not file_path.exists():
            self.dimensions.setText("Dimensions: Missing file")
            self.info_status.setText("Status: File not found")
            self.preview.setText("This image is missing from disk.")
            return
        valid, error = validate_image(file_path)
        if not valid:
            self.dimensions.setText("Dimensions: Invalid image")
            self.info_status.setText(f"Status: {error}")
            self.preview.setText("This file could not be loaded safely.")
            return
        dimensions = get_image_dimensions(file_path)
        if dimensions is not None:
            self.dimensions.setText(f"Dimensions: {dimensions[0]} x {dimensions[1]} px")
        else:
            self.dimensions.setText("Dimensions: Unknown")
        self.info_status.setText("Status: Ready")
        pixmap = QPixmap(str(file_path))
        if pixmap.isNull():
            self.preview.setText("Could not render preview.")
            return
        scaled = pixmap.scaled(520, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview.setPixmap(scaled)
        self.preview.setText("")

    def add_images(self):
        product_id = self.selector.currentData()
        if not product_id:
            QMessageBox.information(self, "Select product", "Create or select a product first.")
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Select images", "", "Images (*.jpg *.jpeg *.png *.webp *.gif)")
        if not paths:
            return
        added = 0
        for name in paths:
            try:
                destination = organize_image(Path(name), product_id)
                self.images.add(product_id, str(destination), Path(name).name)
                added += 1
            except (ValueError, OSError) as error:
                QMessageBox.warning(self, "Image not added", f"{Path(name).name}: {error}")
        self.refresh()
        if added:
            self.info_status.setText(f"Status: Added {added} image(s)")

    def remove_image(self):
        item = self.list.currentItem()
        if not item:
            return
        image = item.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "Remove image", "Remove this image from the product?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.images.delete(image.id)
            try:
                Path(image.file_path).unlink(missing_ok=True)
            except OSError:
                pass
            self.refresh()

    def move(self, direction):
        item = self.list.currentItem()
        if item:
            self.images.move(item.data(Qt.ItemDataRole.UserRole).id, direction)
            self.refresh()

    def _process_selected_image(self, action: str) -> None:
        image = self._selected_image()
        if image is None:
            QMessageBox.information(self, "Select image", "Select an image before applying a local edit.")
            return
        file_path = Path(image.file_path)
        if not file_path.exists():
            QMessageBox.warning(self, "Image missing", "This image file is missing from disk and cannot be processed.")
            return
        processed = process_image(file_path, action, max_size=1200)
        if processed is None:
            QMessageBox.warning(self, "Image processing failed", "This image could not be processed locally. It may be corrupted or unsupported.")
            return
        self.info_status.setText(f"Status: {action.title()} applied")
        self.preview.setPixmap(QPixmap(str(processed)).scaled(520, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.preview.setText("")

    def resize_selected_image(self) -> None:
        self._process_selected_image("resize")

    def crop_selected_image(self) -> None:
        self._process_selected_image("crop")

    def rotate_selected_image(self) -> None:
        self._process_selected_image("rotate")

    def optimize_selected_image(self) -> None:
        self._process_selected_image("optimize")
