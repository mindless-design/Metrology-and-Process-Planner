"""Warning records and visibility domain namespace."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from metrology_process_planner.domains.warnings.warnings import WarningRecord

_LAZY_EXPORTS = {
    "is_process_warning": "metrology_process_planner.domains.warnings.warning_visibility",
    "session_is_process_aware": "metrology_process_planner.domains.warnings.warning_visibility",
    "warning_visible_for_session": "metrology_process_planner.domains.warnings.warning_visibility",
}

__all__ = [
    "WarningRecord",
    "is_process_warning",
    "session_is_process_aware",
    "warning_visible_for_session",
]


def __getattr__(name: str) -> Any:
    """Load visibility helpers without creating session-record import cycles."""

    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
