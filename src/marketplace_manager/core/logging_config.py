"""Logging setup for the desktop application."""

import logging

from marketplace_manager.core.activity_logs import sanitize_log_text
from marketplace_manager.core.config import LOG_DIR, load_configuration


class SafeFormatter(logging.Formatter):
    """Format log records after redacting secret-shaped values."""

    def format(self, record: logging.LogRecord) -> str:
        return sanitize_log_text(super().format(record))


def configure_logging() -> None:
    """Configure console and file logging once for the application."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    level_name = load_configuration()
    level = getattr(logging, level_name, logging.INFO)

    formatter = SafeFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = logging.FileHandler(LOG_DIR / "marketplace_manager.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler],
        force=True,
    )
    logging.getLogger(__name__).info("Logging configured")

