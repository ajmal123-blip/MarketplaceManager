"""AI provider interface and offline test provider."""
import os
from typing import Protocol
from marketplace_manager.ai.models import ListingRequest, ListingResult

class AIProvider(Protocol):
    def generate_listing(self, request: ListingRequest) -> ListingResult: ...

class AIServiceUnavailableError(RuntimeError): pass

class UnavailableProvider:
    def generate_listing(self, request: ListingRequest) -> ListingResult:
        raise AIServiceUnavailableError("AI service is not configured. Set AI_PROVIDER and its credentials in your local environment configuration.")

class MockProvider:
    """Deterministic offline provider for tests and local demonstrations."""
    def generate_listing(self, request: ListingRequest) -> ListingResult:
        title=f"{request.condition} {request.product_title}".strip()
        description=f"{request.product_title} in {request.condition.lower()} condition. {request.details}".strip()
        return ListingResult(title, description, description[:140], ", ".join(filter(None,[request.product_title,request.category,request.condition,request.location])))

def get_provider() -> AIProvider:
    """Select a provider without reading or logging secret values."""
    if os.getenv("AI_PROVIDER", "").lower() == "mock": return MockProvider()
    return UnavailableProvider()
