from marketplace_manager.ai.models import ListingRequest
from marketplace_manager.ai.providers import MockProvider, UnavailableProvider, AIServiceUnavailableError

def test_mock_provider_generates_listing_without_network():
    result=MockProvider().generate_listing(ListingRequest("Lamp","Home","New","10","Karachi","LED light"))
    assert result.title == "New Lamp" and "LED light" in result.description and "Home" in result.keywords

def test_unavailable_provider_has_clear_error():
    try: UnavailableProvider().generate_listing(ListingRequest("Lamp","","","","",""))
    except AIServiceUnavailableError as error: assert "not configured" in str(error)
    else: raise AssertionError("Expected unavailable-provider error")
