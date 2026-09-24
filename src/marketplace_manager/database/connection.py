"""SQLite connection management."""

import sqlite3
from pathlib import Path


def create_connection(database_path: Path | str) -> sqlite3.Connection:
    """Open a SQLite connection with safe defaults for this application."""
    if database_path != ":memory:":
        database_path = Path(database_path)
        database_path.parent.mkdir(parents=True, exist_ok=True)
    # Scheduler workers share the application connection under service locks.
    connection = sqlite3.connect(database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
