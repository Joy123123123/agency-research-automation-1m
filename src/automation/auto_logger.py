"""
Automation Logger — Records every automated action to a JSON log file.
The web app reads this log to show the "what happened today" dashboard.
Owner: Md Jamil Islam
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
DEFAULT_LOG_FILE = Path("tracking/automation_log.json")


def _load(log_file: Path) -> list[dict[str, Any]]:
    if log_file.exists():
        try:
            with open(log_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save(entries: list[dict[str, Any]], log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, default=str)


def log_event(
    event_type: str,
    message: str,
    details: dict[str, Any] | None = None,
    log_file: Path = DEFAULT_LOG_FILE,
) -> None:
    """
    Append a single automation event to the log.

    event_type examples: "research", "outreach", "follow_up", "report", "scheduler", "error"
    """
    entry: dict[str, Any] = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "type": event_type,
        "msg": message,
    }
    if details:
        entry["details"] = details

    with _LOCK:
        entries = _load(log_file)
        entries.append(entry)
        # Keep last 500 entries
        if len(entries) > 500:
            entries = entries[-500:]
        _save(entries, log_file)


def today_events(log_file: Path = DEFAULT_LOG_FILE) -> list[dict[str, Any]]:
    """Return all log entries from today."""
    today = date.today().isoformat()
    with _LOCK:
        return [e for e in _load(log_file) if e.get("ts", "").startswith(today)]


def all_events(limit: int = 100, log_file: Path = DEFAULT_LOG_FILE) -> list[dict[str, Any]]:
    """Return the most recent N log entries (newest first)."""
    with _LOCK:
        entries = _load(log_file)
    return list(reversed(entries[-limit:]))
