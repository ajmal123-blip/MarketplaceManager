from datetime import datetime, timedelta

import pytest

from marketplace_manager.database.service import initialize_database
from marketplace_manager.scheduler.service import TASK_TYPES, SchedulerService


def service() -> SchedulerService:
    return SchedulerService(initialize_database(":memory:"))


def test_create_edit_delete_and_persist_scheduled_task() -> None:
    scheduler = service()
    scheduled = datetime.now() + timedelta(hours=1)
    task_id = scheduler.create("Morning export", "Export data", scheduled)
    row = scheduler.get(task_id)
    assert row["task_name"] == "Morning export"
    assert row["task_type"] == "Export data"
    assert row["status"] == "pending"
    assert row["next_run"] == scheduled.isoformat()

    updated = scheduled + timedelta(hours=1)
    assert scheduler.edit(task_id, "Evening export", "Export data", updated) is True
    assert scheduler.get(task_id)["task_name"] == "Evening export"
    assert scheduler.get(task_id)["scheduled_at"] == updated.isoformat()
    assert scheduler.delete(task_id) is True
    assert scheduler.get(task_id) is None


def test_legacy_create_form_and_filters_remain_supported() -> None:
    scheduler = service()
    task_id = scheduler.create("Export data", datetime.now() - timedelta(minutes=1))
    assert scheduler.list_tasks(search="export")[0]["id"] == task_id
    assert scheduler.list_tasks(status="completed") == []


def test_enable_disable_and_due_execution() -> None:
    scheduler = service()
    task_id = scheduler.create("Process images", datetime.now() - timedelta(minutes=1))
    assert scheduler.set_enabled(task_id, False) is True
    assert scheduler.list_tasks()[0]["status"] == "pending"
    scheduler.run_due()
    assert scheduler.list_tasks()[0]["status"] == "pending"
    scheduler.set_enabled(task_id, True)
    scheduler.run_due()
    assert scheduler.list_tasks()[0]["status"] == "completed"
    assert scheduler.list_tasks()[0]["last_run"] is not None
    assert scheduler.history(task_id)[0]["status"] == "completed"


def test_failed_task_is_recorded_without_raising() -> None:
    scheduler = service()

    def failing_handler(_task) -> None:
        raise RuntimeError("simulated local failure")

    scheduler.register_handler("Export data", failing_handler)
    task_id = scheduler.create("Broken export", "Export data", datetime.now() - timedelta(minutes=1))
    assert scheduler.run_task(task_id) is False
    assert scheduler.get(task_id)["status"] == "failed"
    assert scheduler.history(task_id)[0]["message"] == "Internal task failed. No external action was performed."


def test_task_validation_rejects_invalid_values() -> None:
    scheduler = service()
    with pytest.raises(ValueError, match="Task name"):
        scheduler.create("", "Export data", datetime.now())
    with pytest.raises(ValueError, match="Unsupported"):
        scheduler.create("Task", "Unknown", datetime.now())
    with pytest.raises(ValueError, match="local date"):
        scheduler.create("Task", "Export data", datetime.now().astimezone())


def test_only_one_background_worker_and_clean_shutdown() -> None:
    scheduler = service()
    assert scheduler.start_background(interval_seconds=0.1) is True
    assert scheduler.start_background(interval_seconds=0.1) is False
    assert scheduler.is_running is True
    scheduler.shutdown()
    assert scheduler.is_running is False


def test_task_types_are_local_and_supported() -> None:
    assert "Export data" in TASK_TYPES
