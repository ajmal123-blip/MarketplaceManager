"""Safe connection configuration, mock testing, and activity logging."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
import re
import sqlite3
from typing import Callable

CONNECTION_TYPES = ("Facebook", "Marketplace", "Other")
CONNECTION_STATUSES = ("Not tested", "Connected", "Failed", "Disabled")
_ENVIRONMENT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class Connection:
    id: int | None
    name: str
    connection_type: str
    endpoint: str
    secret_ref: str
    enabled: bool
    status: str
    created_at: datetime | None = None
    last_tested: datetime | None = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class ConnectionActivity:
    id: int | None
    connection_id: int | None
    event: str
    created_at: datetime
    message: str


@dataclass(frozen=True, slots=True)
class ConnectionTestResult:
    success: bool
    status: str
    message: str


ConnectionTester = Callable[[Connection], bool]


def validate_connection_values(name: str, connection_type: str, endpoint: str = "", secret_ref: str = "") -> list[str]:
    """Validate only non-secret connection metadata and return UI-safe messages."""
    errors: list[str] = []
    if not name.strip():
        errors.append("Connection name is required.")
    if connection_type not in CONNECTION_TYPES:
        errors.append("Choose a supported connection type.")
    if secret_ref.strip() and not _ENVIRONMENT_NAME.fullmatch(secret_ref.strip()):
        errors.append("Secret reference must be a valid environment variable name.")
    if "password" in secret_ref.lower() or "token" in secret_ref.lower() or "key" in secret_ref.lower():
        # The reference name is allowed; this message is intentionally not based on its value.
        pass
    return errors


def mask_sensitive(value: str) -> str:
    """Return a fixed mask without ever returning any part of the supplied secret."""
    return "••••••" if value else ""


class ConnectionService:
    """Repository-style service for local connection metadata only."""

    def __init__(self, connection: sqlite3.Connection, tester: ConnectionTester | None = None) -> None:
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        self._tester = tester or (lambda _connection: True)

    def create(self, name: str, connection_type: str, endpoint: str = "", secret_ref: str = "") -> Connection:
        self._validate(name, connection_type, endpoint, secret_ref)
        cursor = self.connection.execute(
            """INSERT INTO connections (name, connection_type, endpoint, secret_ref)
               VALUES (?, ?, ?, ?)""",
            (name.strip(), connection_type, endpoint.strip(), secret_ref.strip()),
        )
        self.connection.commit()
        item = self.get(cursor.lastrowid)
        if item is None:
            raise RuntimeError("Connection was created but could not be read")
        self._record(item.id, "Connection created", "Connection metadata created.")
        self.logger.info("Connection %s created", item.id)
        return item

    def get(self, connection_id: int) -> Connection | None:
        row = self.connection.execute("SELECT * FROM connections WHERE id = ?", (connection_id,)).fetchone()
        return self._row_to_connection(row) if row else None

    def list_connections(self, search: str = "", status: str = "All") -> list[Connection]:
        clauses: list[str] = []
        values: list[str] = []
        if search.strip():
            clauses.append("(name LIKE ? OR connection_type LIKE ? OR endpoint LIKE ?)")
            term = f"%{search.strip()}%"
            values.extend((term, term, term))
        if status != "All":
            clauses.append("status = ?")
            values.append(status)
        query = "SELECT * FROM connections"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC, id DESC"
        return [self._row_to_connection(row) for row in self.connection.execute(query, values).fetchall()]

    def update(self, connection_id: int, name: str, connection_type: str, endpoint: str = "", secret_ref: str = "") -> bool:
        self._validate(name, connection_type, endpoint, secret_ref)
        cursor = self.connection.execute(
            """UPDATE connections SET name = ?, connection_type = ?, endpoint = ?, secret_ref = ?
               WHERE id = ?""",
            (name.strip(), connection_type, endpoint.strip(), secret_ref.strip(), connection_id),
        )
        self.connection.commit()
        if cursor.rowcount:
            self._record(connection_id, "Connection updated", "Connection metadata updated.")
            self.logger.info("Connection %s updated", connection_id)
        return cursor.rowcount == 1

    def delete(self, connection_id: int) -> bool:
        item = self.get(connection_id)
        if item is None:
            return False
        cursor = self.connection.execute("DELETE FROM connections WHERE id = ?", (connection_id,))
        self.connection.commit()
        if cursor.rowcount == 1:
            self._record(None, "Connection deleted", "A connection configuration was deleted.")
            self.logger.info("Connection %s deleted", connection_id)
            return True
        return False

    def set_enabled(self, connection_id: int, enabled: bool) -> bool:
        item = self.get(connection_id)
        if item is None:
            return False
        status = item.status if enabled and item.status != "Disabled" else ("Not tested" if enabled else "Disabled")
        cursor = self.connection.execute(
            "UPDATE connections SET enabled = ?, status = ?, message = ? WHERE id = ?",
            (int(enabled), status, "" if enabled else "Connection is disabled.", connection_id),
        )
        self.connection.commit()
        if cursor.rowcount:
            event = "Connection enabled" if enabled else "Connection disabled"
            self._record(connection_id, event, event + ".")
            self.logger.info("Connection %s %s", connection_id, "enabled" if enabled else "disabled")
        return cursor.rowcount == 1

    def test_connection(self, connection_id: int) -> ConnectionTestResult:
        item = self.get(connection_id)
        if item is None:
            return ConnectionTestResult(False, "Failed", "Connection was not found.")
        self._record(connection_id, "Connection test started", "Connection test started.")
        if not item.enabled:
            result = ConnectionTestResult(False, "Disabled", "Enable the connection before testing it.")
            self._finish_test(item.id, result)
            return result
        try:
            success = bool(self._tester(item))
        except Exception:
            success = False
        result = (
            ConnectionTestResult(True, "Connected", "Mock connection test succeeded.")
            if success else ConnectionTestResult(False, "Failed", "Mock connection test failed.")
        )
        self._finish_test(item.id, result)
        return result

    def activity(self, connection_id: int | None = None, limit: int = 100) -> list[ConnectionActivity]:
        if connection_id is None:
            rows = self.connection.execute(
                "SELECT * FROM connection_activity ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM connection_activity WHERE connection_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
                (connection_id, limit),
            ).fetchall()
        return [
            ConnectionActivity(row["id"], row["connection_id"], row["event"], datetime.fromisoformat(row["created_at"]), row["message"])
            for row in rows
        ]

    def _finish_test(self, connection_id: int | None, result: ConnectionTestResult) -> None:
        now = datetime.now().isoformat()
        self.connection.execute(
            "UPDATE connections SET status = ?, last_tested = ?, message = ? WHERE id = ?",
            (result.status, now, result.message, connection_id),
        )
        self.connection.commit()
        event = "Connection test succeeded" if result.success else "Connection test failed"
        self._record(connection_id, event, result.message)
        self.logger.info("Connection %s %s", connection_id, "test succeeded" if result.success else "test failed")

    def _record(self, connection_id: int | None, event: str, message: str) -> None:
        self.connection.execute(
            "INSERT INTO connection_activity (connection_id, event, message) VALUES (?, ?, ?)",
            (connection_id, event, message),
        )
        self.connection.commit()

    @staticmethod
    def _validate(name: str, connection_type: str, endpoint: str, secret_ref: str) -> None:
        errors = validate_connection_values(name, connection_type, endpoint, secret_ref)
        if errors:
            raise ValueError(" ".join(errors))

    @staticmethod
    def _row_to_connection(row: sqlite3.Row) -> Connection:
        return Connection(
            id=row["id"], name=row["name"], connection_type=row["connection_type"], endpoint=row["endpoint"],
            secret_ref=row["secret_ref"], enabled=bool(row["enabled"]), status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_tested=datetime.fromisoformat(row["last_tested"]) if row["last_tested"] else None,
            message=row["message"],
        )
