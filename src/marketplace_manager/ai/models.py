"""AI input and output models."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ListingRequest:
    product_title: str; category: str; condition: str; price: str; location: str; details: str

@dataclass(frozen=True)
class ListingResult:
    title: str; description: str; short_description: str; keywords: str
