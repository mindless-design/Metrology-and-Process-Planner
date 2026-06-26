"""Session editor shell callbacks and rerender helpers."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.ui.session_editor import (
    InMemorySessionEditorWidgetFactory,
    NavigatorFilterState,
    SessionEditorCallbacks,
    SessionEditorShell,
)
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


def default_shell() -> SessionEditorShell:
    """Return the default in-memory shell used by tests and headless adapters."""

    return SessionEditorShell(InMemorySessionEditorWidgetFactory())


def callbacks_for(
    controller: Any,
    filter_state: NavigatorFilterState,
) -> SessionEditorCallbacks:
    """Build shell callbacks for selection, actions, and navigator filters."""

    def on_select(item_id: str) -> None:
        """Handle on select."""
        controller.dispatch_current_action(
            EditorAction(EditorActionType.SELECT_ITEM, "Select", item_id)
        )

    def on_action(action: EditorAction) -> None:
        """Handle on action."""
        controller.dispatch_current_action(action)

    return SessionEditorCallbacks(
        on_select,
        on_action,
        controller.filter_navigator,
        filter_state,
    )


def render_current(controller: Any) -> None:
    """Rerender the current editor window when all shell state is available."""

    if (
        controller.current_document is not None
        and controller.current_window is not None
        and controller._callbacks is not None
    ):
        controller._shell.render(
            controller.current_window,
            controller.current_document,
            controller._adapter,
            controller._callbacks,
        )
