"""Validation independent of the user interface."""

from decimal import Decimal, InvalidOperation


def validate_product_values(title: str, price_text: str, sku: str) -> tuple[float | None, str | None]:
    """Validate required product values and return a safe floating-point price."""
    if not title.strip():
        return None, "Title is required."
    if not sku.strip():
        return None, "SKU is required."
    try:
        price = Decimal(price_text.strip())
    except (InvalidOperation, ValueError):
        return None, "Price must be a valid number."
    if not price.is_finite() or price < 0:
        return None, "Price must be zero or greater."
    return float(price), None
