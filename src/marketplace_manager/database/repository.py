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

    def list_filtered(
        self,
        search: str = "",
        status: str = "All",
        category: str = "All",
        condition: str = "All",
    ) -> list[Product]:
        """Return products matching the supplied search, status, category, and condition filters."""
        clauses: list[str] = []
        values: list[str] = []
        if search.strip():
            clauses.append("(title LIKE ? OR sku LIKE ? OR category LIKE ? OR description LIKE ?)")
            term = f"%{search.strip()}%"
            values.extend([term, term, term, term])
        if status != "All":
            clauses.append("status = ?")
            values.append(status)
        if category != "All":
            clauses.append("category = ?")
            values.append(category)
        if condition != "All":
            clauses.append("condition = ?")
            values.append(condition)
        statement = "SELECT * FROM products"
        if clauses:
            statement += " WHERE " + " AND ".join(clauses)
        statement += " ORDER BY created_at DESC, id DESC"
        rows = self._connection.execute(statement, values).fetchall()
        return [self._row_to_product(row) for row in rows]

    def list_categories(self) -> list[str]:
        rows = self._connection.execute("SELECT DISTINCT category FROM products WHERE category != '' ORDER BY category ASC").fetchall()
        return [row[0] for row in rows]

    def list_conditions(self) -> list[str]:
        rows = self._connection.execute("SELECT DISTINCT condition FROM products WHERE condition != '' ORDER BY condition ASC").fetchall()
        return [row[0] for row in rows]

    def counts_by_status(self) -> dict[str, int]:
        total = self._connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        rows = self._connection.execute("SELECT status, COUNT(*) AS count FROM products GROUP BY status").fetchall()
        counts = {"total": total, "draft": 0, "active": 0, "archived": 0}
        for row in rows:
            status = str(row[0]).lower()
            if status in counts:
                counts[status] = int(row[1])
        return counts

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
