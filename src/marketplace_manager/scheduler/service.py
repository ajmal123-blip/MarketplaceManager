"""Thread-safe local scheduling for internal application tasks."""

from __future__ import annotations

from datetime import datetime
import logging
import sqlite3
from threading import Event, RLock, Thread
from typing import Callable

TASK_TYPES = ("Generate listing text", "Process images", "Prepare a listing", "Export data")
TASK_STATUSES = ("pending", "running", "completed", "failed", "disabled")

TaskHandler = Callable[[sqlite3.Row], None]


class SchedulerService:
    """Persist and execute local tasks without external automation services."""

    def __init__(self, connection: sqlite3.Connection, handlers: dict[str, TaskHandler] | None = None) -> None:
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        self._lock = RLock()
        self._handlers = handlers or {}
        self._stop_event = Event()
        self._worker: Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def create(
        self,
        task_name: str,
        task_type_or_scheduled_at: str | datetime,
        scheduled_at: datetime | None = None,
    ) -> int:
        """Create a task, accepting the Phase 3 ``(type, datetime)`` form too."""
        if isinstance(task_type_or_scheduled_at, datetime):
            task_type = task_name
            scheduled_at = task_type_or_scheduled_at
            task_name = task_type
        else:
            task_type = task_type_or_scheduled_at
        self._validate(task_name, task_type, scheduled_at)
        assert scheduled_at is not None
        with self._lock:
            cursor = self.connection.execute(
                """INSERT INTO scheduled_tasks
                   (task_name, task_type, scheduled_at, next_run, status, enabled)
                   VALUES (?, ?, ?, ?, 'pending', 1)""",
                (task_name.strip(), task_type, scheduled_at.isoformat(), scheduled_at.isoformat()),
            )
            self.connection.commit()
            return int(cursor.lastrowid)

    def get(self, task_id: int) -> sqlite3.Row | None:
        with self._lock:
            return self.connection.execute("SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,)).fetchone()

    def list_tasks(self, search: str = "", status: str = "All", enabled: bool | None = None) -> list[sqlite3.Row]:
        clauses: list[str] = []
        values: list[object] = []
        if search.strip():
            clauses.append("(task_name LIKE ? OR task_type LIKE ?)")
            term = f"%{search.strip()}%"
            values.extend((term, term))
        if status != "All":
            clauses.append("status = ?")
            values.append(status.lower())
        if enabled is not None:
            clauses.append("enabled = ?")
            values.append(int(enabled))
        statement = "SELECT * FROM scheduled_tasks"
        if clauses:
            statement += " WHERE " + " AND ".join(clauses)
        statement += " ORDER BY scheduled_at ASC, id ASC"
        with self._lock:
            return self.connection.execute(statement, values).fetchall()

    def edit(self, task_id: int, task_name: str, task_type: str, scheduled_at: datetime) -> bool:
        self._validate(task_name, task_type, scheduled_at)
        with self._lock:
            cursor = self.connection.execute(
                """UPDATE scheduled_tasks SET task_name = ?, task_type = ?, scheduled_at = ?,
                   next_run = CASE WHEN enabled = 1 THEN ? ELSE NULL END,
                   status = CASE WHEN enabled = 1 THEN 'pending' ELSE status END,
                   updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
                (task_name.strip(), task_type, scheduled_at.isoformat(), scheduled_at.isoformat(), task_id),
            )
            self.connection.commit()
            return cursor.rowcount == 1

    def set_enabled(self, task_id: int, enabled: bool) -> bool:
        with self._lock:
            row = self.connection.execute("SELECT status, scheduled_at FROM scheduled_tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                return False
            # Keep legacy pending status for disabled tasks; the UI exposes the disabled state separately.
            status = "pending" if enabled and row["status"] == "disabled" else row["status"]
            next_run = row["scheduled_at"] if enabled else None
            self.connection.execute(
                "UPDATE scheduled_tasks SET enabled = ?, status = ?, next_run = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(enabled), status, next_run, task_id),
            )
            self.connection.commit()
            return True

    def delete(self, task_id: int) -> bool:
        with self._lock:
            cursor = self.connection.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
            self.connection.commit()
            return cursor.rowcount == 1

    def history(self, task_id: int) -> list[sqlite3.Row]:
        with self._lock:
            return self.connection.execute(
                "SELECT * FROM task_history WHERE task_id = ? ORDER BY executed_at DESC, id DESC", (task_id,)
            ).fetchall()

    def register_handler(self, task_type: str, handler: TaskHandler) -> None:
        if task_type not in TASK_TYPES:
            raise ValueError("Unsupported internal task type.")
        self._handlers[task_type] = handler

    def run_due(self, now: datetime | None = None) -> None:
        current = now or datetime.now()
        with self._lock:
            rows = self.connection.execute(
                "SELECT id FROM scheduled_tasks WHERE enabled = 1 AND status = 'pending' AND scheduled_at <= ?",
                (current.isoformat(),),
            ).fetchall()
        for row in rows:
            self.run_task(row["id"], current)

    def run_task(self, task_id: int, now: datetime | None = None) -> bool:
        current = now or datetime.now()
        with self._lock:
            task = self.connection.execute("SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,)).fetchone()
            if task is None or not task["enabled"] or task["status"] not in {"pending", "failed"}:
                return False
            self.connection.execute(
                "UPDATE scheduled_tasks SET status = 'running', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,)
            )
            self.connection.commit()
        try:
            handler = self._handlers.get(task["task_type"], self._default_handler)
            handler(task)
        except Exception:
            with self._lock:
                self.connection.execute(
                    "UPDATE scheduled_tasks SET status = 'failed', last_run = ?, next_run = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (current.isoformat(), task_id),
                )
                self.connection.execute(
                    "INSERT INTO task_history (task_id, status, message) VALUES (?, 'failed', ?)",
                    (task_id, "Internal task failed. No external action was performed."),
                )
                self.connection.commit()
            self.logger.error("Scheduled task %s failed", task_id)
            return False
        with self._lock:
            message = f"Completed internal task: {task['task_type']}"
            self.connection.execute(
                "UPDATE scheduled_tasks SET status = 'completed', last_run = ?, next_run = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (current.isoformat(), task_id),
            )
            self.connection.execute(
                "INSERT INTO task_history (task_id, status, message) VALUES (?, 'completed', ?)", (task_id, message)
            )
            self.connection.commit()
        self.logger.info("Scheduled task %s completed", task_id)
        return True

    def start_background(self, interval_seconds: float = 1.0) -> bool:
        """Start one daemon worker; repeated calls never create duplicate workers."""
        if self.is_running:
            return False
        self._stop_event.clear()
        self._worker = Thread(target=self._worker_loop, args=(interval_seconds,), name="marketplace-scheduler", daemon=True)
        self._worker.start()
        return True

    def shutdown(self, timeout: float = 2.0) -> None:
        """Stop the worker and wait briefly so application shutdown remains clean."""
        self._stop_event.set()
        worker = self._worker
        if worker is not None and worker is not __import__("threading").current_thread():
            worker.join(timeout)
        self._worker = None

    def _worker_loop(self, interval_seconds: float) -> None:
        while not self._stop_event.wait(max(0.1, interval_seconds)):
            try:
                self.run_due()
            except Exception:
                self.logger.error("Scheduler worker cycle failed")

    @staticmethod
    def _default_handler(task: sqlite3.Row) -> None:
        """Safe local no-op for supported internal task types."""
        return None

    @staticmethod
    def _validate(task_name: str, task_type: str, scheduled_at: datetime | None) -> None:
        if not task_name.strip():
            raise ValueError("Task name is required.")
        if task_type not in TASK_TYPES:
            raise ValueError("Unsupported internal task type.")
        if not isinstance(scheduled_at, datetime) or scheduled_at.tzinfo is not None:
            raise ValueError("Scheduled date and time must be a valid local date and time.")
