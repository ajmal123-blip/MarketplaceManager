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


def test_product_repository_category_and_condition_filter() -> None:
    connection = initialize_database(":memory:")
    repository = ProductRepository(connection)
    repository.create(Product(None, "Dining Chair", "Oak chair", 85.0, "Furniture", "Used", "Karachi", "CHAIR-100", "active"))
    repository.create(Product(None, "Desk Lamp", "Warm lamp", 24.0, "Home", "New", "Lahore", "LAMP-200", "draft"))
    repository.create(Product(None, "Office Chair", "Blue chair", 90.0, "Furniture", "Used", "Islamabad", "CHAIR-300", "active"))

    matching = repository.list_filtered(search="chair", category="Furniture", condition="Used", status="active")
    assert [item.sku for item in matching] == ["CHAIR-300", "CHAIR-100"]

    no_match = repository.list_filtered(category="Home", condition="Used")
    assert no_match == []
    connection.close()
