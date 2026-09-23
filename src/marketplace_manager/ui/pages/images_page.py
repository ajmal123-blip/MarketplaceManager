"""Local product image management page."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget
from marketplace_manager.database.image_repository import ImageRepository
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.images.service import organize_image
from marketplace_manager.ui.pages.common import page_header

class ImagesPage(QWidget):
    def __init__(self):
        super().__init__(); self.connection=initialize_database(); self.products=ProductRepository(self.connection); self.images=ImageRepository(self.connection)
        layout=QVBoxLayout(self); layout.setContentsMargins(36,32,36,32); page_header(layout,"Images","Organize local product images.")
        self.selector=QComboBox(); layout.addWidget(self.selector); self.selector.currentIndexChanged.connect(self.refresh)
        body=QHBoxLayout(); self.list=QListWidget(); self.preview=QLabel("Select an image to preview"); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setMinimumSize(320,240); body.addWidget(self.list,1); body.addWidget(self.preview,1); layout.addLayout(body,1)
        buttons=QHBoxLayout(); add=QPushButton("Add Images"); remove=QPushButton("Remove"); up=QPushButton("Move Up"); down=QPushButton("Move Down"); refresh=QPushButton("Refresh")
        for button in (add,remove,up,down,refresh): buttons.addWidget(button)
        buttons.addStretch(); layout.addLayout(buttons); add.clicked.connect(self.add_images); remove.clicked.connect(self.remove_image); up.clicked.connect(lambda:self.move(-1)); down.clicked.connect(lambda:self.move(1)); refresh.clicked.connect(self.load_products); self.list.currentRowChanged.connect(self.show_preview); self.load_products()
    def load_products(self):
        self.selector.blockSignals(True); self.selector.clear()
        for product in self.products.list_all(): self.selector.addItem(product.title, product.id)
        self.selector.blockSignals(False); self.refresh()
    def refresh(self):
        self.list.clear(); product_id=self.selector.currentData()
        if not product_id: return
        for image in self.images.list_for_product(product_id): self.list.addItem(image.original_name); self.list.item(self.list.count()-1).setData(Qt.ItemDataRole.UserRole,image)
        self.preview.setPixmap(QPixmap())
    def show_preview(self, row):
        item=self.list.item(row)
        if not item: return
        pixmap=QPixmap(item.data(Qt.ItemDataRole.UserRole).file_path)
        self.preview.setPixmap(pixmap.scaled(320,240,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    def add_images(self):
        product_id=self.selector.currentData()
        if not product_id: QMessageBox.information(self,"Select product","Create or select a product first."); return
        paths,_=QFileDialog.getOpenFileNames(self,"Select images","","Images (*.jpg *.jpeg *.png *.webp *.gif)")
        for name in paths:
            try:
                destination=organize_image(Path(name),product_id); self.images.add(product_id,str(destination),Path(name).name)
            except (ValueError,OSError) as error: QMessageBox.warning(self,"Image not added",f"{Path(name).name}: {error}")
        self.refresh()
    def remove_image(self):
        item=self.list.currentItem()
        if not item: return
        image=item.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self,"Remove image","Remove this image from the product?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            self.images.delete(image.id)
            try: Path(image.file_path).unlink(missing_ok=True)
            except OSError: pass
            self.refresh()
    def move(self,direction):
        item=self.list.currentItem()
        if item: self.images.move(item.data(Qt.ItemDataRole.UserRole).id,direction); self.refresh()
