"""AI input/output models and provider-independent validation."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class ListingRequest:
    product_title: str
    category: str
    condition: str
    price: str
    location: str
    details: str


@dataclass(frozen=True, slots=True)
class ListingResult:
    title: str
    description: str
    short_description: str
    keywords: str


def validate_listing_request(request: ListingRequest) -> list[str]:
    """Return user-facing validation messages without making a provider call."""
    errors: list[str] = []
    fields = (
        ("Product title", request.product_title),
        ("Category", request.category),
        ("Condition", request.condition),
        ("Price", request.price),
        ("Location", request.location),
        ("Product details", request.details),
    )
    for label, value in fields:
        if not value.strip():
            errors.append(f"{label} is required.")
    if request.price.strip():
        try:
            price = Decimal(request.price.strip())
            if not price.is_finite() or price < 0:
                errors.append("Price must be zero or greater.")
        except (InvalidOperation, ValueError):
            errors.append("Price must be a valid number.")
    return errors
