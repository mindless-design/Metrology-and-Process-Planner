"""Callback type aliases for the generic session editor shell."""

from __future__ import annotations

from collections.abc import Callable

from metrology_process_planner.workflows.editor.view_models import EditorAction

SelectionCallback = Callable[[str], None]
ActionCallback = Callable[[EditorAction], None]
