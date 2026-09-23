"""Database location configuration."""

from pathlib import Path

from marketplace_manager.core.config import DATA_DIR


DEFAULT_DATABASE_PATH: Path = DATA_DIR / "marketplace_manager.sqlite"

