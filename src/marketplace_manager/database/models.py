"""Data models used by the database layer."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Product:
    """A locally stored marketplace product."""

    id: int | None
    title: str
    description: str
    price: float
    category: str
    condition: str
    location: str
    sku: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

