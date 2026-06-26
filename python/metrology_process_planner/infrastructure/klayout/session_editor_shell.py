"""KLayout/Qt widget factory for the unified session editor shell."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.infrastructure.klayout.session_editor_regions import (
    render_action_region,
    render_metadata_region,
    render_text_region,
)
from metrology_process_planner.ui.session_editor.navigator import (
    NavigatorFilterCallback,
    NavigatorFilterState,
    NavigatorRows,
)
from metrology_process_planner.ui.session_editor.sections import MetadataRows, PreviewRows
from metrology_process_planner.ui.session_editor.shell import (
    ActionCallback,
    InMemorySessionEditorWidgetFactory,
    SelectionCallback,
)
from metrology_process_planner.workflows.editor.view_models import EditorAction


class KLayoutSessionEditorWidgetFactory(InMemorySessionEditorWidgetFactory):
    """Render editor regions with Qt widgets while retaining testable region state."""

    def __init__(self, pya_module: Any) -> None:
        self._pya = pya_module

    def create_window(self, title: str) -> Any:
        """Create a KLayout/Qt top-level editor window."""

        widget_class = getattr(self._pya, "QWidget", None)
        if widget_class is None:
            return super().create_window(title)
        window = widget_class()
        _call(window, "setWindowTitle", title)
        _set_region(window, "title", title)
        _set_region(window, "shown", False)
        _install_root_layout(self._pya, window)
        return window

    def set_header(self, window: Any, entries: tuple[tuple[str, str], ...]) -> None:
        """Render header entries as a compact state-backed region."""

        _set_region(window, "header", entries)
        render_text_region(self._pya, window, "header", entries)

    def set_primary_actions(
        self,
        window: Any,
        actions: tuple[EditorAction, ...],
        on_action: ActionCallback,
    ) -> None:
        """Render primary actions and preserve the routed callback."""

        _set_region(window, "primary_actions", actions)
        _set_region(window, "on_primary_action", on_action)
        render_action_region(self._pya, window, "primary_actions", actions)

    def set_navigator(
        self,
        window: Any,
        groups: NavigatorRows,
        selected_item_id: str,
        on_select: SelectionCallback,
        on_filter: NavigatorFilterCallback | None,
        filter_state: NavigatorFilterState,
    ) -> None:
        """Render navigator rows and preserve selection/filter callbacks."""

        _set_region(window, "navigator", groups)
        _set_region(window, "selected_item_id", selected_item_id)
        _set_region(window, "on_select", on_select)
        _set_region(window, "navigator_filter", filter_state)
        _set_region(window, "on_filter_navigator", on_filter)
        render_text_region(self._pya, window, "navigator", groups)

    def set_preview(self, window: Any, previews: PreviewRows) -> None:
        """Render the center preview/details region."""

        _set_region(window, "preview", previews)
        render_text_region(self._pya, window, "preview", previews)

    def set_inspector(
        self,
        window: Any,
        fields: MetadataRows,
        actions: tuple[EditorAction, ...],
        on_action: ActionCallback,
    ) -> None:
        """Render inspector fields/actions and preserve the routed callback."""

        _set_region(
            window,
            "fields",
            tuple((field.key, field.label, field.value) for field in fields),
        )
        _set_region(window, "metadata_fields", fields)
        _set_region(window, "actions", actions)
        _set_region(window, "on_action", on_action)
        render_metadata_region(
            self._pya,
            window,
            "fields",
            fields,
            _selected_item_id(window),
            on_action,
        )
        render_action_region(self._pya, window, "actions", actions)

    def set_status(self, window: Any, text: str) -> None:
        """Render bottom status text."""

        _set_region(window, "status", text)
        render_text_region(self._pya, window, "status", (text,))

    def show(self, window: Any) -> None:
        """Show the editor window."""

        _set_region(window, "shown", True)
        _call(window, "show")


def _set_region(window: Any, key: str, value: Any) -> None:
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


def _selected_item_id(window: Any) -> str:
    if isinstance(window, dict):
        return str(window.get("selected_item_id", ""))
    state = getattr(window, "_mpp_state", {})
    return str(state.get("selected_item_id", ""))


def _install_root_layout(pya: Any, window: Any) -> None:
    layout_class = getattr(pya, "QVBoxLayout", None)
    if layout_class is None:
        return
    layout = layout_class()
    _set_region(window, "qt_layout", layout)
    _call(window, "setLayout", layout)


def _call(target: Any, name: str, *args: Any) -> None:
    method = getattr(target, name, None)
    if callable(method):
        method(*args)
