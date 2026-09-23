"""Logging setup for the desktop application."""

import logging

from marketplace_manager.core.config import LOG_DIR, load_configuration


def configure_logging() -> None:
    """Configure console and file logging once for the application."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    level_name = load_configuration()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "marketplace_manager.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    logging.getLogger(__name__).info("Logging configured")

