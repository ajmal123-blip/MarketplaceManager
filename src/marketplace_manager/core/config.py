"""Central locations and environment configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"


def load_configuration() -> str:
    """Load local environment settings and return the configured log level."""
    load_dotenv(PROJECT_ROOT / ".env")
    return os.getenv("APP_LOG_LEVEL", "INFO").upper()

