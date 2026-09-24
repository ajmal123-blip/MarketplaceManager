"""AI provider interface and offline test provider."""
from typing import Protocol

from marketplace_manager.ai.models import ListingRequest, ListingResult
from marketplace_manager.core.config import load_app_settings


class AIProvider(Protocol):
    def generate_listing(self, request: ListingRequest) -> ListingResult: ...


class AIServiceUnavailableError(RuntimeError):
    pass


class UnavailableProvider:
    def generate_listing(self, request: ListingRequest) -> ListingResult:
        raise AIServiceUnavailableError(
            "AI service is not configured. Set AI_PROVIDER in your local environment configuration."
        )


class MockProvider:
    """Deterministic offline provider for tests and local demonstrations."""

    def generate_listing(self, request: ListingRequest) -> ListingResult:
        title = f"{request.condition} {request.product_title}".strip()
        description = f"{request.product_title} in {request.condition.lower()} condition. {request.details}".strip()
        return ListingResult(
            title,
            description,
            description[:140],
            ", ".join(filter(None, [request.product_title, request.category, request.condition, request.location])),
        )


def get_provider() -> AIProvider:
    """Select a provider without reading or logging secret values."""
    provider_name = load_app_settings().ai_provider.lower()
    if provider_name == "mock":
        return MockProvider()
    return UnavailableProvider()
