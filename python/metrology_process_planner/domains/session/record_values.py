"""Small value coercion helpers for session records."""

from __future__ import annotations

from typing import Any, Optional


def optional_int(value: Any) -> Optional[int]:
    """Return an optional integer from saved data."""

    return None if value is None else int(value)


def optional_str(value: Any) -> Optional[str]:
    """Return an optional string from saved data."""

    return None if value is None else str(value)
