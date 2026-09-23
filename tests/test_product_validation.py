"""Tests for product input validation and repository filtering."""
from marketplace_manager.database.models import Product
from marketplace_manager.database.repository import ProductRepository
from marketplace_manager.database.service import initialize_database
from marketplace_manager.products.validation import validate_product_values


def test_product_validation_rejects_missing_title_and_invalid_price() -> None:
    assert validate_product_values("", "10", "SKU")[1] == "Title is required."
    assert validate_product_values("Lamp", "not-a-price", "SKU")[1] == "Price must be a valid number."
    assert validate_product_values("Lamp", "-1", "SKU")[1] == "Price must be zero or greater."


def test_product_repository_search_and_status_filter() -> None:
    connection = initialize_database(":memory:"); repository = ProductRepository(connection)
    repository.create(Product(None, "Wooden Chair", "", 40, "Furniture", "Used", "Karachi", "CHAIR-1", "active"))
    repository.create(Product(None, "LED Lamp", "", 12, "Home", "New", "Lahore", "LAMP-1", "draft"))
    assert [product.sku for product in repository.list_filtered("lamp")] == ["LAMP-1"]
    assert [product.sku for product in repository.list_filtered(status="active")] == ["CHAIR-1"]
    connection.close()
