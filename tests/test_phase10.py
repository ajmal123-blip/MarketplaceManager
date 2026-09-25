"""Phase 10 activity log and settings regression tests."""

import logging

from PySide6.QtWidgets import QApplication

from marketplace_manager.core.activity_logs import ActivityLogService
from marketplace_manager.core.config import AppSettings, load_app_settings, save_app_settings
from marketplace_manager.core.logging_config import SafeFormatter
from marketplace_manager.ui.pages.activity_logs_page import ActivityLogsPage
from marketplace_manager.ui.pages.settings_page import SettingsPage


def test_activity_logs_load_filter_and_redact(tmp_path) -> None:
    path = tmp_path / "activity.log"
    path.write_text(
        "2026-09-25 10:00:00,000 | INFO | app.main | Started\n"
        "2026-09-25 10:01:00,000 | WARNING | scheduler | token=super-secret retrying\n"
        "not a log line\n"
        "2026-09-25 10:02:00,000 | ERROR | app.main | Failed\n",
        encoding="utf-8",
    )

    service = ActivityLogService(path)
    entries = service.read(level="warning")

    assert len(entries) == 1
    assert entries[0].message == "token=[REDACTED] retrying"
    assert len(service.read(search="failed", component="APP.MAIN")) == 0
    assert len(service.read(search="failed", component="app.main")) == 1


def test_activity_logs_clear_missing_file_is_safe(tmp_path) -> None:
    service = ActivityLogService(tmp_path / "missing.log")
    assert service.read() == []
    service.clear()
    assert service.read() == []


def test_logging_formatter_redacts_secrets() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "api_key=%s", ("secret-value",), None)
    assert "secret-value" not in SafeFormatter("%(message)s").format(record)
    assert "[REDACTED]" in SafeFormatter("%(message)s").format(record)


def test_phase10_pages_load_and_settings_persist(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    activity_page = ActivityLogsPage(tmp_path / "empty.log")
    assert activity_page.table.rowCount() == 0
    assert activity_page.level_filter.count() == 5

    settings_path = tmp_path / "settings.json"
    original = AppSettings(workspace_name="Phase 10", default_product_status="active")
    save_app_settings(original, settings_path)
    assert load_app_settings(settings_path) == original

    settings_page = SettingsPage()
    assert settings_page.ai_secret_value.echoMode() != settings_page.ai_secret_value.EchoMode.Normal
    assert settings_page.theme.currentText() == "FBauto Blue/Grey/Purple"
    settings_page.close()
    activity_page.close()
    app.processEvents()
