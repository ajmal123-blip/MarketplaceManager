"""Reliable, local scheduled task storage and execution."""
import logging
import sqlite3
from datetime import datetime

TASK_TYPES=("Generate listing text","Process images","Prepare a listing","Export data")

class SchedulerService:
    def __init__(self, connection: sqlite3.Connection): self.connection=connection; self.logger=logging.getLogger(__name__)
    def create(self, task_type: str, scheduled_at: datetime) -> int:
        if task_type not in TASK_TYPES: raise ValueError("Unsupported internal task type.")
        return self.connection.execute("INSERT INTO scheduled_tasks (task_type, scheduled_at) VALUES (?, ?)",(task_type,scheduled_at.isoformat())).lastrowid
    def list_tasks(self): return self.connection.execute("SELECT * FROM scheduled_tasks ORDER BY scheduled_at").fetchall()
    def set_enabled(self, task_id:int, enabled:bool): self.connection.execute("UPDATE scheduled_tasks SET enabled=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",(int(enabled),task_id)); self.connection.commit()
    def delete(self,task_id:int): self.connection.execute("DELETE FROM scheduled_tasks WHERE id=?",(task_id,)); self.connection.commit()
    def history(self,task_id:int): return self.connection.execute("SELECT * FROM task_history WHERE task_id=? ORDER BY executed_at DESC",(task_id,)).fetchall()
    def run_due(self, now:datetime|None=None):
        now=now or datetime.now(); rows=self.connection.execute("SELECT * FROM scheduled_tasks WHERE enabled=1 AND status='pending' AND scheduled_at<=?",(now.isoformat(),)).fetchall()
        for task in rows: self.run_task(task["id"])
    def run_task(self,task_id:int):
        task=self.connection.execute("SELECT * FROM scheduled_tasks WHERE id=?",(task_id,)).fetchone()
        if not task: return
        try:
            message=f"Completed internal task: {task['task_type']}"; status="completed"
            self.connection.execute("UPDATE scheduled_tasks SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",(status,task_id)); self.connection.execute("INSERT INTO task_history (task_id,status,message) VALUES (?,?,?)",(task_id,status,message)); self.connection.commit(); self.logger.info(message)
        except Exception as error:
            self.connection.execute("UPDATE scheduled_tasks SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE id=?",(task_id,)); self.connection.execute("INSERT INTO task_history (task_id,status,message) VALUES (?, 'failed', ?)",(task_id,"Internal task failed. Check application logs.")); self.connection.commit(); self.logger.exception("Task %s failed",task_id)
