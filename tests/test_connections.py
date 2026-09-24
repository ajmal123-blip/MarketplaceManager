import logging

import pytest

from marketplace_manager.connections.service import (
    CONNECTION_TYPES,
    ConnectionService,
    mask_sensitive,
    validate_connection_values,
)
from marketplace_manager.database.service import initialize_database


def service(tester=None) -> ConnectionService:
    return ConnectionService(initialize_database(":memory:"), tester=tester)


def test_create_edit_delete_connection_and_activity() -> None:
    connections = service()
    item = connections.create("Local marketplace", "Marketplace", "local://marketplace", "MARKETPLACE_KEY")
    assert item.id is not None
    assert item.name == "Local marketplace"
    assert item.secret_ref == "MARKETPLACE_KEY"
    assert connections.get(item.id).endpoint == "local://marketplace"

    assert connections.update(item.id, "Edited marketplace", "Other", "local://edited", "OTHER_SECRET") is True
    assert connections.get(item.id).name == "Edited marketplace"
    assert connections.get(item.id).connection_type == "Other"
    assert [entry.event for entry in connections.activity(item.id)][:2] == ["Connection updated", "Connection created"]

    assert connections.delete(item.id) is True
    assert connections.get(item.id) is None
    assert connections.activity(None)[0].event == "Connection deleted"


def test_connection_validation_and_safe_masking() -> None:
    errors = validate_connection_values("", "Unknown", "", "not a valid ref")
    assert "Connection name is required." in errors
    assert "Choose a supported connection type." in errors
    assert "valid environment variable" in errors[-1]
    with pytest.raises(ValueError, match="Connection name"):
        service().create("", CONNECTION_TYPES[0])
    assert mask_sensitive("super-secret-token") == "••••••"
    assert "super-secret-token" not in mask_sensitive("super-secret-token")
    assert mask_sensitive("") == ""


def test_enable_disable_and_mock_test_connection() -> None:
    connections = service()
    item = connections.create("Mock marketplace", "Marketplace")
    assert connections.set_enabled(item.id, False) is True
    result = connections.test_connection(item.id)
    assert result.success is False
    assert result.status == "Disabled"
    assert connections.set_enabled(item.id, True) is True
    result = connections.test_connection(item.id)
    assert result.success is True
    assert result.status == "Connected"
    assert connections.get(item.id).last_tested is not None
    assert connections.activity(item.id)[0].event == "Connection test succeeded"


def test_mock_test_failure_does_not_raise_or_log_secrets(caplog) -> None:
    secret = "do-not-log-this-secret"

    def failing_tester(_connection) -> bool:
        raise RuntimeError(secret)

    connections = service(failing_tester)
    item = connections.create("Failing mock", "Other", secret_ref="TEST_SECRET")
    with caplog.at_level(logging.INFO):
        result = connections.test_connection(item.id)
    assert result.success is False
    assert result.status == "Failed"
    assert secret not in caplog.text
    assert secret not in connections.activity(item.id)[0].message
    assert connections.get(item.id).message == "Mock connection test failed."


def test_search_and_status_filter() -> None:
    connections = service()
    first = connections.create("Facebook placeholder", "Facebook")
    connections.create("Other placeholder", "Other")
    connections.test_connection(first.id)
    assert len(connections.list_connections(search="facebook")) == 1
    assert connections.list_connections(status="Connected")[0].name == "Facebook placeholder"
