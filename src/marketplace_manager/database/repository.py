"""Parameterized product CRUD operations."""

import sqlite3
from datetime import datetime

from marketplace_manager.database.models import Product


class ProductRepository:
    """Database operations for products; no UI concerns belong here."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, product: Product) -> Product:
        cursor = self._connection.execute(
            """INSERT INTO products (title, description, price, category, condition, location, sku, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (product.title, product.description, product.price, product.category, product.condition,
             product.location, product.sku, product.status),
        )
        self._connection.commit()
        created = self.get(cursor.lastrowid)
        if created is None:  # Defensive guard for an unexpected SQLite failure.
            raise RuntimeError("Product was created but could not be read")
        return created

    def get(self, product_id: int) -> Product | None:
        row = self._connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return self._row_to_product(row) if row else None

    def list_all(self) -> list[Product]:
        rows = self._connection.execute("SELECT * FROM products ORDER BY created_at DESC, id DESC").fetchall()
        return [self._row_to_product(row) for row in rows]

    def list_filtered(self, search: str = "", status: str = "All") -> list[Product]:
        """Return products matching a title, SKU, or category search and status."""
        clauses: list[str] = []
        values: list[str] = []
        if search.strip():
            clauses.append("(title LIKE ? OR sku LIKE ? OR category LIKE ?)")
            term = f"%{search.strip()}%"
            values.extend([term, term, term])
        if status != "All":
            clauses.append("status = ?")
            values.append(status)
        statement = "SELECT * FROM products"
        if clauses:
            statement += " WHERE " + " AND ".join(clauses)
        statement += " ORDER BY created_at DESC, id DESC"
        rows = self._connection.execute(statement, values).fetchall()
        return [self._row_to_product(row) for row in rows]

    def update(self, product: Product) -> Product | None:
        if product.id is None:
            raise ValueError("A product id is required for an update")
        self._connection.execute(
            """UPDATE products SET title = ?, description = ?, price = ?, category = ?, condition = ?,
               location = ?, sku = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (product.title, product.description, product.price, product.category, product.condition,
             product.location, product.sku, product.status, product.id),
        )
        self._connection.commit()
        return self.get(product.id)

    def delete(self, product_id: int) -> bool:
        cursor = self._connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self._connection.commit()
        return cursor.rowcount == 1

    @staticmethod
    def _row_to_product(row: sqlite3.Row) -> Product:
        return Product(
            id=row["id"], title=row["title"], description=row["description"], price=row["price"],
            category=row["category"], condition=row["condition"], location=row["location"],
            sku=row["sku"], status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]), updated_at=datetime.fromisoformat(row["updated_at"]),
        )
