"""Persistence for CSV and Excel import results."""

from dataclasses import dataclass
from datetime import datetime
import sqlite3


@dataclass(frozen=True, slots=True)
class ImportHistory:
    id: int | None
    imported_at: datetime
    file_name: str
    file_type: str
    records: int
    successful_records: int
    failed_records: int
    status: str
    message: str = ""


class ImportHistoryRepository:
    """Database operations for import history; independent from the UI."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def record(self, file_name: str, file_type: str, records: int, successful_records: int,
               failed_records: int, status: str, message: str = "") -> ImportHistory:
        cursor = self._connection.execute(
            """INSERT INTO import_history
               (file_name, file_type, records, successful_records, failed_records, status, message)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (file_name, file_type, records, successful_records, failed_records, status, message),
        )
        self._connection.commit()
        return self.get(cursor.lastrowid)  # type: ignore[return-value]

    def list_recent(self, limit: int = 100) -> list[ImportHistory]:
        rows = self._connection.execute(
            "SELECT * FROM import_history ORDER BY imported_at DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_history(row) for row in rows]

    def get(self, history_id: int) -> ImportHistory | None:
        row = self._connection.execute("SELECT * FROM import_history WHERE id = ?", (history_id,)).fetchone()
        return self._row_to_history(row) if row else None

    @staticmethod
    def _row_to_history(row: sqlite3.Row) -> ImportHistory:
        return ImportHistory(
            id=row["id"], imported_at=datetime.fromisoformat(row["imported_at"]),
            file_name=row["file_name"], file_type=row["file_type"], records=row["records"],
            successful_records=row["successful_records"], failed_records=row["failed_records"],
            status=row["status"], message=row["message"],
        )