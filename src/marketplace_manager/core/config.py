"""Central locations and safe, environment-aware application configuration."""

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _runtime_root() -> Path:
    """Use a writable per-user root for frozen builds and the repo during development."""
    if getattr(sys, "frozen", False):
        local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return local_app_data / "FBauto Bot 33"
    return PROJECT_ROOT


RUNTIME_ROOT = _runtime_root()
DATA_DIR = RUNTIME_ROOT / "data"
LOG_DIR = RUNTIME_ROOT / "logs"
SETTINGS_PATH = DATA_DIR / "app_settings.json"
THEME_NAME = "FBauto Blue/Grey/Purple"
VALID_STARTUP_BEHAVIORS = ("Normal", "Start minimized")
VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")

DEFAULT_APP_SETTINGS = {
    "workspace_name": "FBauto Bot 33",
    "default_currency": "USD",
    "default_location": "Local workspace",
    "default_product_status": "draft",
    "ai_provider": "mock",
    "startup_behavior": "Normal",
    "confirm_before_delete": True,
    "theme": THEME_NAME,
    "compact_ui": False,
    "ai_secret_env_var": "",
    "notifications_enabled": True,
    "notify_on_task_failure": True,
    "log_level": "INFO",
    "log_retention_days": 30,
    "show_connection_activity": True,
}


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Local preferences; secret values are intentionally not represented."""

    workspace_name: str = "FBauto Bot 33"
    default_currency: str = "USD"
    default_location: str = "Local workspace"
    default_product_status: str = "draft"
    ai_provider: str = "mock"
    startup_behavior: str = "Normal"
    confirm_before_delete: bool = True
    theme: str = THEME_NAME
    compact_ui: bool = False
    ai_secret_env_var: str = ""
    notifications_enabled: bool = True
    notify_on_task_failure: bool = True
    log_level: str = "INFO"
    log_retention_days: int = 30
    show_connection_activity: bool = True

    def to_dict(self) -> dict[str, object]:
        """Return JSON-safe settings without any secret value."""
        return asdict(self)


def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.strip().lower() in {"1", "true", "yes", "on"}:
            return True
        if value.strip().lower() in {"0", "false", "no", "off"}:
            return False
    return default


def _resolved_settings_dict(path: Path | str | None = None) -> dict[str, object]:
    """Load settings from environment, then disk, then safe defaults."""
    load_dotenv(PROJECT_ROOT / ".env")
    base: dict[str, object] = DEFAULT_APP_SETTINGS.copy()
    if path is not None:
        settings_path = Path(path)
        if settings_path.exists():
            try:
                loaded = json.loads(settings_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    base.update({key: value for key, value in loaded.items() if key in base and value is not None})
            except (OSError, ValueError, TypeError):
                pass

    environment_keys = {
        "workspace_name": "APP_WORKSPACE_NAME",
        "default_currency": "DEFAULT_CURRENCY",
        "default_location": "DEFAULT_LOCATION",
        "default_product_status": "DEFAULT_PRODUCT_STATUS",
        "ai_provider": "AI_PROVIDER",
        "startup_behavior": "APP_STARTUP_BEHAVIOR",
        "theme": "APP_THEME",
        "ai_secret_env_var": "AI_SECRET_ENV_VAR",
        "log_level": "APP_LOG_LEVEL",
    }
    for key, env_name in environment_keys.items():
        value = os.getenv(env_name)
        if value is not None and value.strip():
            base[key] = value.strip()
    return base


def load_app_settings(path: Path | str | None = SETTINGS_PATH) -> AppSettings:
    values = _resolved_settings_dict(path)
    try:
        retention = int(values.get("log_retention_days", 30))
    except (TypeError, ValueError):
        retention = 30
    return AppSettings(
        workspace_name=str(values.get("workspace_name", DEFAULT_APP_SETTINGS["workspace_name"])),
        default_currency=str(values.get("default_currency", DEFAULT_APP_SETTINGS["default_currency"])),
        default_location=str(values.get("default_location", DEFAULT_APP_SETTINGS["default_location"])),
        default_product_status=str(values.get("default_product_status", DEFAULT_APP_SETTINGS["default_product_status"])),
        ai_provider=str(values.get("ai_provider", DEFAULT_APP_SETTINGS["ai_provider"])),
        startup_behavior=str(values.get("startup_behavior", DEFAULT_APP_SETTINGS["startup_behavior"])),
        confirm_before_delete=_as_bool(values.get("confirm_before_delete"), True),
        theme=str(values.get("theme", THEME_NAME)),
        compact_ui=_as_bool(values.get("compact_ui"), False),
        ai_secret_env_var=str(values.get("ai_secret_env_var", "")),
        notifications_enabled=_as_bool(values.get("notifications_enabled"), True),
        notify_on_task_failure=_as_bool(values.get("notify_on_task_failure"), True),
        log_level=str(values.get("log_level", "INFO")).upper(),
        log_retention_days=retention,
        show_connection_activity=_as_bool(values.get("show_connection_activity"), True),
    )


def validate_app_settings(settings: AppSettings) -> list[str]:
    """Return user-facing validation errors without inspecting secret values."""
    errors: list[str] = []
    if not settings.workspace_name.strip():
        errors.append("Application name is required.")
    if settings.startup_behavior not in VALID_STARTUP_BEHAVIORS:
        errors.append("Choose a valid startup behavior.")
    if settings.theme != THEME_NAME:
        errors.append("The current FBauto blue/grey/purple theme is required.")
    if settings.default_product_status not in {"draft", "active", "archived"}:
        errors.append("Default product status must be draft, active, or archived.")
    if settings.log_level not in VALID_LOG_LEVELS:
        errors.append("Log level must be DEBUG, INFO, WARNING, or ERROR.")
    if settings.log_retention_days < 0 or settings.log_retention_days > 3650:
        errors.append("Log retention must be between 0 and 3650 days.")
    return errors


def save_app_settings(settings: AppSettings, path: Path | str = SETTINGS_PATH) -> Path:
    errors = validate_app_settings(settings)
    if errors:
        raise ValueError(" ".join(errors))
    settings_path = Path(path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
    return settings_path


def load_configuration() -> str:
    """Return the configured safe log level for the existing logging system."""
    return load_app_settings().log_level
