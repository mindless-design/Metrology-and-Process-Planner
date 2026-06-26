"""Window-registry helper for the diagnostics controller."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from metrology_process_planner.app.diagnostics_dashboard_rows import with_open_window_rows
from metrology_process_planner.app.diagnostics_windows import open_windows_summary
from metrology_process_planner.app.window_registry import WindowOpenStatus


def open_or_refresh_diagnostics_window(
    controller: Any,
    result: Any,
    recent_events: tuple[object, ...],
) -> Any:
    """Open or refresh the diagnostics shell through the shared window registry."""

    registry_result = controller._window_registry.get_or_create_diagnostics_panel(
        controller.active_session.id,
        "Advanced Diagnostics",
        lambda: controller._shell.open(result, recent_events),
        refresh_existing=lambda window: controller._shell.render(window, result, recent_events),
    )
    if registry_result.status is WindowOpenStatus.FAILED:
        return result.__class__("failed", registry_result.message)
    if registry_result.window is not None:
        rows = with_open_window_rows(
            result.summary_rows,
            open_windows_summary(controller._window_registry),
        )
        result = replace(result, summary_rows=rows)
        controller._shell.render(registry_result.window, result, recent_events)
        controller._shell.set_action_callback(registry_result.window, controller.route_action)
    status = "raised" if registry_result.status is WindowOpenStatus.RAISED else result.status
    return replace(result, status=status, window=registry_result.window)
