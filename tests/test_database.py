"""Tests for SQLite initialization and product CRUD."""

from marketplace_manager.database.models import Product
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database


def product() -> Product:
    return Product(None, "Desk lamp", "Warm white LED lamp", 24.99, "Home", "Used", "Karachi", "LAMP-001", "draft")


def test_database_initialization_creates_products_table() -> None:
    connection = initialize_database(":memory:")
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    connection.close()
    assert {"products", "schema_migrations"} <= tables


def test_product_crud() -> None:
    connection = initialize_database(":memory:")
    repository = ProductRepository(connection)
    created = repository.create(product())
    assert created.id is not None and created.title == "Desk lamp"
    updated = repository.update(Product(created.id, "Modern desk lamp", created.description, 30.0, created.category, created.condition, created.location, created.sku, "active"))
    assert updated is not None and updated.price == 30.0 and updated.status == "active"
    assert repository.list_all() == [updated]
    assert repository.delete(created.id) is True
    assert repository.get(created.id) is None
    connection.close()
