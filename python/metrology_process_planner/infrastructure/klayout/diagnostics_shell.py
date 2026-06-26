"""KLayout/Qt Advanced Diagnostics shell factory."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.diagnostics import DiagnosticEvent
from metrology_process_planner.infrastructure.klayout.session_editor_regions import (
    render_text_region,
)
from metrology_process_planner.ui.diagnostics.dashboard import DiagnosticsDashboardModel
from metrology_process_planner.ui.shell.view_models import EditorActionViewModel


class KLayoutDiagnosticsWidgetFactory:
    """Render diagnostics rows, events, and actions with Qt widgets when available."""

    def __init__(self, pya_module: Any) -> None:
        self._pya = pya_module

    def create_window(self, title: str) -> Any:
        """Create a diagnostics window."""

        widget_class = getattr(self._pya, "QWidget", None)
        if widget_class is None:
            return _fallback_window(title)
        window = widget_class()
        _call(window, "setWindowTitle", title)
        _set_state(window, "title", title)
        _install_layout(self._pya, window)
        return window

    def set_summary(self, window: Any, entries: tuple[tuple[str, str], ...]) -> None:
        """Render summary rows."""

        _set_state(window, "diagnostics_summary", entries)
        render_text_region(self._pya, window, "diagnostics_summary", entries)

    def set_dashboard(self, window: Any, dashboard: DiagnosticsDashboardModel) -> None:
        """Render grouped dashboard sections."""

        rows = tuple(_dashboard_row(section.title, row.label, row.value)
                     for section in dashboard.sections for row in section.rows)
        _set_state(window, "diagnostics_dashboard", dashboard)
        _set_state(window, "diagnostics_dashboard_rows", rows)
        render_text_region(self._pya, window, "diagnostics_dashboard", rows)

    def set_events(self, window: Any, events: tuple[DiagnosticEvent, ...]) -> None:
        """Render recent diagnostic events."""

        rows = tuple(_event_row(event) for event in events[-25:])
        _set_state(window, "diagnostics_events", rows)
        render_text_region(self._pya, window, "diagnostics_events", rows)

    def set_actions(self, window: Any, actions: tuple[EditorActionViewModel, ...]) -> None:
        """Render diagnostics action rows."""

        rows = tuple(_action_row(action) for action in actions)
        _set_state(window, "diagnostics_actions", actions)
        _set_state(window, "diagnostics_action_rows", rows)
        render_text_region(self._pya, window, "diagnostics_actions", rows)

    def set_action_callback(self, window: Any, callback: Any) -> None:
        """Store action callback for the modeless shell."""

        _set_state(window, "on_action", callback)

    def show(self, window: Any) -> None:
        """Show the diagnostics window."""

        _set_state(window, "shown", True)
        _call(window, "show")


def _fallback_window(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "shown": False,
        "resizable": True,
        "scrollable": True,
        "minimum_size": (840, 620),
        "fits_1366x768": True,
    }


def _event_row(event: DiagnosticEvent) -> str:
    return " | ".join(
        item
        for item in (event.severity, event.category, event.operation, event.event_name)
        if item
    )


def _dashboard_row(section_title: str, label: str, value: str) -> str:
    return f"{section_title} | {label} | {value}"


def _action_row(action: EditorActionViewModel) -> str:
    suffix = "" if action.enabled else f" ({action.disabled_reason})"
    return f"{action.label}{suffix}"


def _install_layout(pya: Any, window: Any) -> None:
    layout_class = getattr(pya, "QVBoxLayout", None)
    if layout_class is None:
        return
    layout = layout_class()
    _set_state(window, "qt_layout", layout)
    _call(window, "setLayout", layout)


def _set_state(window: Any, key: str, value: Any) -> None:
    if isinstance(window, dict):
        window[key] = value
        return
    state = getattr(window, "_mpp_state", None)
    if state is None:
        state = {}
        try:
            window._mpp_state = state
        except Exception:  # noqa: BLE001 - Qt wrappers may reject dynamic attrs.
            return
    state[key] = value


def _call(target: Any, name: str, *args: Any) -> None:
    method = getattr(target, name, None)
    if callable(method):
        method(*args)
