"""Data models for the generic session editor shell."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.ui.session_editor.navigator import (
    NavigatorFilterCallback,
    NavigatorFilterState,
)
from metrology_process_planner.ui.session_editor.shell_types import (
    ActionCallback,
    SelectionCallback,
)


@dataclass(frozen=True)
class SessionEditorCallbacks:
    """Callbacks emitted by the editor shell for selection and actions."""

    on_select_item: SelectionCallback
    on_action: ActionCallback
    on_filter_navigator: NavigatorFilterCallback | None = None
    navigator_filter: NavigatorFilterState = NavigatorFilterState()
