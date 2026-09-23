"""Database initialization entry point."""

import sqlite3
from pathlib import Path

from marketplace_manager.database.config import DEFAULT_DATABASE_PATH
from marketplace_manager.database.connection import create_connection
from marketplace_manager.database.migrations import apply_migrations


def initialize_database(database_path: Path | str = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Open a database and bring its schema up to the latest migration."""
    connection = create_connection(database_path)
    apply_migrations(connection)
    return connection
