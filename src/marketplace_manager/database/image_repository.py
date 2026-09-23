"""SQLite metadata operations for product images."""
import sqlite3
from dataclasses import dataclass

@dataclass(frozen=True)
class ProductImage: id: int; product_id: int; file_path: str; original_name: str; position: int

class ImageRepository:
    def __init__(self, connection: sqlite3.Connection): self._connection = connection
    def list_for_product(self, product_id: int) -> list[ProductImage]:
        return [ProductImage(row["id"], row["product_id"], row["file_path"], row["original_name"], row["position"]) for row in self._connection.execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY position", (product_id,))]
    def add(self, product_id: int, file_path: str, original_name: str) -> ProductImage:
        position = len(self.list_for_product(product_id)); cursor = self._connection.execute("INSERT INTO product_images (product_id, file_path, original_name, position) VALUES (?, ?, ?, ?)", (product_id, file_path, original_name, position)); self._connection.commit(); return ProductImage(cursor.lastrowid, product_id, file_path, original_name, position)
    def delete(self, image_id: int) -> bool:
        cursor = self._connection.execute("DELETE FROM product_images WHERE id = ?", (image_id,)); self._connection.commit(); return cursor.rowcount == 1
    def move(self, image_id: int, direction: int) -> None:
        image = next((item for product_id in self._connection.execute("SELECT product_id FROM product_images WHERE id=?", (image_id,)) for item in self.list_for_product(product_id[0]) if item.id == image_id), None)
        if not image: return
        images = self.list_for_product(image.product_id); target = image.position + direction
        if not 0 <= target < len(images): return
        other = images[target]; self._connection.execute("UPDATE product_images SET position=? WHERE id=?", (other.position, image.id)); self._connection.execute("UPDATE product_images SET position=? WHERE id=?", (image.position, other.id)); self._connection.commit()
