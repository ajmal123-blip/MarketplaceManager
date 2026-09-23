from datetime import datetime, timedelta
from marketplace_manager.database.service import initialize_database
from marketplace_manager.scheduler.service import SchedulerService

def test_scheduled_task_status_and_history():
    service=SchedulerService(initialize_database(":memory:")); task_id=service.create("Export data",datetime.now()-timedelta(minutes=1)); service.run_due()
    assert service.list_tasks()[0]["status"] == "completed" and service.history(task_id)[0]["status"] == "completed"

def test_disabled_task_does_not_run():
    service=SchedulerService(initialize_database(":memory:")); task_id=service.create("Process images",datetime.now()-timedelta(minutes=1)); service.set_enabled(task_id,False); service.run_due()
    assert service.list_tasks()[0]["status"] == "pending"
