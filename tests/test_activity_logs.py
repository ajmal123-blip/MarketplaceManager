from pathlib import Path

from marketplace_manager.core.activity_logs import ActivityLogService, sanitize_log_text


def test_activity_logs_load_search_and_filter(tmp_path: Path) -> None:
    path = tmp_path / "marketplace_manager.log"
    path.write_text(
        "2026-09-25 10:00:00,000 | INFO | marketplace_manager.app | Started\n"
        "2026-09-25 10:01:00,000 | WARNING | marketplace_manager.scheduler | Task needs attention\n"
        "2026-09-25 10:02:00,000 | ERROR | marketplace_manager.connections | token=top-secret failed\n"
        "not a structured log\n",
        encoding="utf-8",
    )
    service = ActivityLogService(path)
    assert len(service.read()) == 3
    assert len(service.read(level="WARNING")) == 1
    assert len(service.read(component="marketplace_manager.scheduler")) == 1
    assert len(service.read(search="attention")) == 1
    assert "top-secret" not in service.read()[2].message
    assert "token=[REDACTED]" in service.read()[2].message


def test_missing_and_empty_logs_are_safe_and_clearable(tmp_path: Path) -> None:
    path = tmp_path / "missing.log"
    service = ActivityLogService(path)
    assert service.read() == []
    service.clear()
    assert path.exists()
    assert service.read() == []
    path.write_text("2026 | DEBUG | test | detail\n", encoding="utf-8")
    service.clear()
    assert path.read_text(encoding="utf-8") == ""


def test_secret_sanitizer_redacts_bearer_and_key_values() -> None:
    safe = sanitize_log_text("api_key=abc123 Bearer xyz789 password=hunter2")
    assert "abc123" not in safe
    assert "xyz789" not in safe
    assert "hunter2" not in safe
    assert "[REDACTED]" in safe
