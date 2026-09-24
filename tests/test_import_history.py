from marketplace_manager.database.import_history_repository import ImportHistoryRepository
from marketplace_manager.database.service import initialize_database


def test_import_history_records_and_lists_results() -> None:
    connection = initialize_database(":memory:")
    repository = ImportHistoryRepository(connection)
    item = repository.record("products.csv", "CSV", 4, 3, 1, "Completed with errors", "One invalid row")
    assert item.id is not None
    recent = repository.list_recent()
    assert len(recent) == 1
    assert recent[0].file_name == "products.csv"
    assert recent[0].records == 4
    assert recent[0].successful_records == 3
    assert recent[0].failed_records == 1
    assert recent[0].status == "Completed with errors"
    connection.close()
