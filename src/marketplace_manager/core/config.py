"""Central locations and environment configuration."""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
SETTINGS_PATH = DATA_DIR / "app_settings.json"

DEFAULT_APP_SETTINGS = {
    "workspace_name": "Marketplace Manager",
    "default_currency": "USD",
    "default_location": "Local workspace",
    "default_product_status": "draft",
    "ai_provider": "mock",
}


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Local, non-secret application settings stored on disk."""

    workspace_name: str = "Marketplace Manager"
    default_currency: str = "USD"
    default_location: str = "Local workspace"
    default_product_status: str = "draft"
    ai_provider: str = "mock"

    def to_dict(self) -> dict[str, str]:
        """Return the settings as JSON-safe values."""
        return {key: value for key, value in asdict(self).items()}


def _resolved_settings_dict(path: Path | str | None = None) -> dict[str, str]:
    """Load values from the environment, then the on-disk settings file, then defaults."""
    load_dotenv(PROJECT_ROOT / ".env")

    base = DEFAULT_APP_SETTINGS.copy()
    if path is not None:
        settings_path = Path(path)
        if settings_path.exists():
            try:
                loaded = json.loads(settings_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    base.update({key: value for key, value in loaded.items() if value is not None})
            except (OSError, ValueError, TypeError):
                pass

    for key, env_name in {
        "workspace_name": "APP_WORKSPACE_NAME",
        "default_currency": "DEFAULT_CURRENCY",
        "default_location": "DEFAULT_LOCATION",
        "default_product_status": "DEFAULT_PRODUCT_STATUS",
        "ai_provider": "AI_PROVIDER",
    }.items():
        value = os.getenv(env_name)
        if value is not None and value.strip():
            base[key] = value.strip()

    return {key: str(value) for key, value in base.items()}


def load_app_settings(path: Path | str | None = SETTINGS_PATH) -> AppSettings:
    """Load the application settings from config sources without exposing secrets."""
    values = _resolved_settings_dict(path)
    return AppSettings(
        workspace_name=values.get("workspace_name", DEFAULT_APP_SETTINGS["workspace_name"]),
        default_currency=values.get("default_currency", DEFAULT_APP_SETTINGS["default_currency"]),
        default_location=values.get("default_location", DEFAULT_APP_SETTINGS["default_location"]),
        default_product_status=values.get("default_product_status", DEFAULT_APP_SETTINGS["default_product_status"]),
        ai_provider=values.get("ai_provider", DEFAULT_APP_SETTINGS["ai_provider"]),
    )


def save_app_settings(settings: AppSettings, path: Path | str = SETTINGS_PATH) -> Path:
    """Write local app settings to disk without storing secrets in source files."""
    settings_path = Path(path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
    return settings_path


def load_configuration() -> str:
    """Load local environment settings and return the configured log level."""
    load_dotenv(PROJECT_ROOT / ".env")
    return os.getenv("APP_LOG_LEVEL", "INFO").upper()

