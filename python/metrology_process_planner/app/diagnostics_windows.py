"""Open-window diagnostics summary helpers."""

from __future__ import annotations

from metrology_process_planner.app.window_registry import WindowRegistry


def open_windows_summary(window_registry: WindowRegistry[object] | None) -> str:
    """Return a compact open-window summary for diagnostics."""

    if window_registry is None:
        return "none"
    rows = []
    for key in window_registry:
        record = window_registry.record_for(key)
        if record is not None:
            rows.append(f"{record.title} [{record.key}]")
    return "; ".join(rows) if rows else "none"
