from marketplace_manager.ai.models import ListingRequest, validate_listing_request
from marketplace_manager.ai.providers import AIServiceUnavailableError, MockProvider, UnavailableProvider, get_provider
from marketplace_manager.database.listing_repository import ListingDraft, ListingDraftRepository
from marketplace_manager.database.service import initialize_database


def valid_request() -> ListingRequest:
    return ListingRequest("Desk lamp", "Home", "Used", "24.99", "Karachi", "Warm LED light with metal shade")


def test_listing_request_validation_reports_missing_and_invalid_price() -> None:
    errors = validate_listing_request(ListingRequest("", "Home", "Used", "not-a-price", "", ""))
    assert "Product title is required." in errors
    assert "Location is required." in errors
    assert "Product details is required." in errors
    assert "Price must be a valid number." in errors


def test_mock_provider_generates_all_listing_fields_without_network() -> None:
    result = MockProvider().generate_listing(valid_request())
    assert result.title
    assert result.description
    assert result.short_description
    assert "Home" in result.keywords


def test_missing_or_unknown_provider_fails_without_exposing_secrets() -> None:
    for provider in (UnavailableProvider(), get_provider("unknown-provider")):
        try:
            provider.generate_listing(valid_request())
        except AIServiceUnavailableError as error:
            message = str(error)
            assert "not configured" in message
            assert "API" not in message
        else:
            raise AssertionError("Expected unavailable-provider error")


def test_listing_draft_repository_saves_and_lists_local_drafts() -> None:
    connection = initialize_database(":memory:")
    repository = ListingDraftRepository(connection)
    saved = repository.create(ListingDraft(None, "Title", "Description", "Short", "lamp, home"))
    assert saved.id is not None
    assert repository.get(saved.id) == saved
    assert repository.list_recent()[0].title == "Title"
    connection.close()


def test_ai_writer_page_generates_with_injected_mock_provider() -> None:
    from PySide6.QtWidgets import QApplication

    from marketplace_manager.ui.pages.ai_writer_page import AIWriterPage

    app = QApplication.instance() or QApplication([])
    page = AIWriterPage(provider=MockProvider())
    page.product_title.setText("Desk lamp")
    page.category.setText("Home")
    page.condition.setText("Used")
    page.price.setText("24.99")
    page.location.setText("Karachi")
    page.details.setPlainText("Warm LED light with metal shade")
    assert page.generate() is True
    assert page.generated_title.text() == "Used Desk lamp"
    assert page.generated_description.toPlainText()
    page.close()
    app.processEvents()
