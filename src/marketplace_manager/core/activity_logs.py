"""Reader and safe maintenance helpers for the existing application log file."""

from dataclasses import dataclass
from pathlib import Path
import re

from marketplace_manager.core.config import LOG_DIR

LOG_LEVELS = ("INFO", "WARNING", "ERROR", "DEBUG")
_SECRET_PATTERN = re.compile(
    r"(?i)(password|passwd|token|api[_ -]?key|secret|cookie|authorization)\s*[:=]\s*[^\s,;]+"
)
_BEARER_PATTERN = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+")


@dataclass(frozen=True, slots=True)
class ActivityLogEntry:
    timestamp: str
    level: str
    component: str
    message: str


def sanitize_log_text(text: str) -> str:
    """Redact common secret-shaped values before any text reaches the UI."""
    redacted = _SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", text)
    return _BEARER_PATTERN.sub("Bearer [REDACTED]", redacted)


class ActivityLogService:
    """Read, filter, and safely clear the log produced by logging_config."""

    def __init__(self, log_path: Path | str | None = None) -> None:
        self.log_path = Path(log_path) if log_path is not None else LOG_DIR / "marketplace_manager.log"

    def read(self, search: str = "", level: str = "All", component: str = "All") -> list[ActivityLogEntry]:
        if not self.log_path.exists():
            return []
        try:
            lines = self.log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        entries = [entry for line in lines if (entry := self.parse_line(line)) is not None]
        search_term = search.strip().lower()
        selected_level = level.strip().upper() if level.strip().lower() != "all" else "All"
        selected_component = component.strip() if component.strip().lower() != "all" else "All"
        return [
            entry for entry in entries
            if (selected_level == "All" or entry.level == selected_level)
            and (selected_component == "All" or entry.component == selected_component)
            and (not search_term or search_term in " ".join((entry.component, entry.message, entry.level)).lower())
        ]

    def components(self) -> list[str]:
        return sorted({entry.component for entry in self.read()})

    def clear(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.write_text("", encoding="utf-8")

    @staticmethod
    def parse_line(line: str) -> ActivityLogEntry | None:
        if not line.strip():
            return None
        parts = line.split(" | ", 3)
        if len(parts) != 4:
            return None
        timestamp, level, component, message = parts
        normalized_level = level.strip().upper()
        if normalized_level not in LOG_LEVELS:
            return None
        return ActivityLogEntry(timestamp.strip(), normalized_level, component.strip(), sanitize_log_text(message.strip()))
