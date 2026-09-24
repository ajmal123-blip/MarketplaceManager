"""Small, ordered SQLite migrations for future schema changes."""

import sqlite3


def _create_products_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            price REAL NOT NULL CHECK (price >= 0),
            category TEXT NOT NULL DEFAULT '',
            condition TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            sku TEXT NOT NULL DEFAULT '' UNIQUE,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _create_product_images_table(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
        file_path TEXT NOT NULL, original_name TEXT NOT NULL, position INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )""")

def _create_listing_drafts_table(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS listing_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL,
        short_description TEXT NOT NULL, keywords TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")

def _create_scheduled_tasks_tables(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS scheduled_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_type TEXT NOT NULL, scheduled_at TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS task_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER NOT NULL, status TEXT NOT NULL, message TEXT NOT NULL,
        executed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(task_id) REFERENCES scheduled_tasks(id) ON DELETE CASCADE)""")


def _create_import_history_table(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS import_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        records INTEGER NOT NULL DEFAULT 0,
        successful_records INTEGER NOT NULL DEFAULT 0,
        failed_records INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        message TEXT NOT NULL DEFAULT ''
    )""")


MIGRATIONS: tuple[tuple[int, callable], ...] = (
    (1, _create_products_table),
    (2, _create_product_images_table),
    (3, _create_listing_drafts_table),
    (4, _create_scheduled_tasks_tables),
    (5, _create_import_history_table),
)


def apply_migrations(connection: sqlite3.Connection) -> None:
    """Apply each unapplied migration inside a transaction."""
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    applied = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
    for version, migration in MIGRATIONS:
        if version not in applied:
            migration(connection)
            connection.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
    connection.commit()
