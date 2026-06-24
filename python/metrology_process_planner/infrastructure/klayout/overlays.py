"""KLayout-safe overlay command sink for persistent canvas objects."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

from metrology_process_planner.workflows.overlays import OverlayCommand, OverlayCommandKind

MarkerFactory = Callable[[OverlayCommand], Any]


class KLayoutOverlayBackend:
    """Store KLayout marker or annotation handles without editing layout data."""

    def __init__(self, marker_factory: Optional[MarkerFactory] = None) -> None:
        self._marker_factory = marker_factory
        self._handles: dict[str, Any] = {}
        self._commands: list[OverlayCommand] = []

    @property
    def commands(self) -> tuple[OverlayCommand, ...]:
        """Return overlay commands applied by this backend."""

        return tuple(self._commands)

    def apply(self, command: OverlayCommand) -> None:
        """Apply one overlay command through marker handles only."""

        self._commands.append(command)
        if command.kind is OverlayCommandKind.REMOVE_OBJECT:
            self._handles.pop(command.object_id, None)
            return
        if command.kind is OverlayCommandKind.HIDE_OBJECT:
            self._handles.pop(command.object_id, None)
            return
        if self._marker_factory is not None and command.canvas_object is not None:
            self._handles[command.object_id] = self._marker_factory(command)
