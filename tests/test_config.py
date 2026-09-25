"""Foundation-level tests."""

import json

from marketplace_manager.core.config import (
    DATA_DIR,
    LOG_DIR,
    PROJECT_ROOT,
    AppSettings,
    load_app_settings,
    save_app_settings,
    validate_app_settings,
)


def test_project_paths_are_based_at_repository_root() -> None:
    """The app keeps generated files in predictable project folders."""
    assert PROJECT_ROOT.name == "MarketplaceManager"
    assert DATA_DIR == PROJECT_ROOT / "data"
    assert LOG_DIR == PROJECT_ROOT / "logs"


def test_app_settings_use_environment_values_and_default_values() -> None:
    """Local app defaults are loaded from the environment or sensible project defaults."""
    settings = AppSettings(
        workspace_name="Demo Workspace",
        default_currency="EUR",
        default_location="Berlin",
        default_product_status="active",
        ai_provider="mock",
    )

    assert settings.workspace_name == "Demo Workspace"
    assert settings.default_currency == "EUR"
    assert settings.default_location == "Berlin"
    assert settings.default_product_status == "active"
    assert settings.ai_provider == "mock"


def test_app_settings_can_be_saved_and_loaded(tmp_path) -> None:
    """The app persists local defaults without storing secrets in source files."""
    path = tmp_path / "settings.json"
    settings = AppSettings(
        workspace_name="Local Store",
        default_currency="USD",
        default_location="New York",
        default_product_status="draft",
        ai_provider="mock",
    )

    save_app_settings(settings, path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["workspace_name"] == "Local Store"
    assert payload["default_currency"] == "USD"
    assert payload["default_location"] == "New York"
    assert payload["default_product_status"] == "draft"
    assert payload["ai_provider"] == "mock"

    reloaded = load_app_settings(path)
    assert reloaded == settings


def test_extended_settings_persist_and_validate_without_secret_values(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = AppSettings(
        workspace_name="Operations",
        default_currency="EUR",
        default_location="Berlin",
        default_product_status="active",
        ai_provider="mock",
        startup_behavior="Start minimized",
        confirm_before_delete=False,
        compact_ui=True,
        ai_secret_env_var="MARKETPLACE_API_KEY",
        notifications_enabled=False,
        notify_on_task_failure=False,
        log_level="DEBUG",
        log_retention_days=90,
        show_connection_activity=False,
    )
    save_app_settings(settings, path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "actual-secret" not in json.dumps(payload)
    assert load_app_settings(path) == settings


def test_settings_validation_rejects_unsafe_values() -> None:
    invalid = AppSettings(log_level="TRACE", log_retention_days=-1, default_product_status="unknown")
    errors = validate_app_settings(invalid)
    assert any("Log level" in error for error in errors)
    assert any("retention" in error for error in errors)
    assert any("product status" in error for error in errors)
