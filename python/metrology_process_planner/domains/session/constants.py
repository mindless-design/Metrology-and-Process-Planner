"""Shared constants and time helpers for session records."""

from __future__ import annotations

from datetime import datetime, timezone

SESSION_SCHEMA_VERSION = "5.0.0"
LEGACY_SESSION_SCHEMA_VERSION = 4


def utc_now_iso() -> str:
    """Return the current UTC timestamp in the saved-session format."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
