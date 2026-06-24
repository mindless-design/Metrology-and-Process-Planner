"""Fakeable overlay command management for persistent canvas objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol

from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasVisualFlag,
    SessionRecord,
)


class OverlayCommandKind(str, Enum):
    """Commands emitted by the pure overlay manager to a backend."""

    CREATE_PREVIEW = "create_preview"
    UPDATE_PREVIEW = "update_preview"
    COMMIT_OBJECT = "commit_object"
    REMOVE_OBJECT = "remove_object"
    SELECT_OBJECT = "select_object"
    ACTIVE_PARENT = "active_parent"
    HIDE_OBJECT = "hide_object"
    SHOW_OBJECT = "show_object"
    MARK_STALE = "mark_stale"
    MARK_INVALID = "mark_invalid"
    RESTORE_OBJECT = "restore_object"


@dataclass(frozen=True)
class OverlayCommand:
    """One overlay backend command for a canvas object."""

    kind: OverlayCommandKind
    object_id: str
    canvas_object: Optional[CanvasObject] = None


class CanvasOverlayBackend(Protocol):
    """Backend contract implemented by KLayout markers or test fakes."""

    def apply(self, command: OverlayCommand) -> None:
        """Apply one overlay command without mutating source layout data."""


class CanvasOverlayManager:
    """Translate canvas object state into overlay backend commands."""

    def __init__(self, backend: CanvasOverlayBackend) -> None:
        self._backend = backend

    def show_live_preview(self, canvas_object: CanvasObject) -> None:
        """Create a live preview overlay for a transient canvas object."""

        self._apply(OverlayCommandKind.CREATE_PREVIEW, canvas_object)

    def update_live_preview(self, canvas_object: CanvasObject) -> None:
        """Update a live preview overlay as its geometry changes."""

        self._apply(OverlayCommandKind.UPDATE_PREVIEW, canvas_object)

    def commit_object(self, canvas_object: CanvasObject) -> None:
        """Commit a pending or saved canvas object overlay."""

        self._apply(OverlayCommandKind.COMMIT_OBJECT, canvas_object)

    def remove_object(self, object_id: str) -> None:
        """Remove one canvas object overlay by id."""

        self._backend.apply(OverlayCommand(OverlayCommandKind.REMOVE_OBJECT, object_id))

    def select_object(self, canvas_object: CanvasObject) -> None:
        """Highlight one selected canvas object overlay."""

        self._apply(OverlayCommandKind.SELECT_OBJECT, canvas_object)

    def set_active_parent(self, canvas_object: CanvasObject) -> None:
        """Highlight one canvas object as the active parent context."""

        self._apply(OverlayCommandKind.ACTIVE_PARENT, canvas_object)

    def hide_object(self, object_id: str) -> None:
        """Hide one canvas object overlay by id."""

        self._backend.apply(OverlayCommand(OverlayCommandKind.HIDE_OBJECT, object_id))

    def show_object(self, canvas_object: CanvasObject) -> None:
        """Show one hidden canvas object overlay."""

        self._apply(OverlayCommandKind.SHOW_OBJECT, canvas_object)

    def mark_stale(self, canvas_object: CanvasObject) -> None:
        """Mark one canvas object overlay as stale."""

        self._apply(OverlayCommandKind.MARK_STALE, canvas_object)

    def mark_invalid(self, canvas_object: CanvasObject) -> None:
        """Mark one canvas object overlay as invalid."""

        self._apply(OverlayCommandKind.MARK_INVALID, canvas_object)

    def restore_session(self, session: SessionRecord) -> None:
        """Restore pending and saved overlays from persistent session state."""

        for canvas_object in session.canvas_objects:
            if _is_hidden(canvas_object):
                self.hide_object(canvas_object.id)
                continue
            self._apply(OverlayCommandKind.RESTORE_OBJECT, canvas_object)
            self._apply_visual_flags(canvas_object)

    def _apply_visual_flags(self, canvas_object: CanvasObject) -> None:
        if CanvasVisualFlag.SELECTED in canvas_object.visual_state:
            self.select_object(canvas_object)
        if CanvasVisualFlag.ACTIVE_PARENT in canvas_object.visual_state:
            self.set_active_parent(canvas_object)
        if canvas_object.stale or CanvasVisualFlag.STALE in canvas_object.visual_state:
            self.mark_stale(canvas_object)
        if CanvasVisualFlag.INVALID in canvas_object.visual_state:
            self.mark_invalid(canvas_object)

    def _apply(self, kind: OverlayCommandKind, canvas_object: CanvasObject) -> None:
        self._backend.apply(OverlayCommand(kind, canvas_object.id, canvas_object))


def _is_hidden(canvas_object: CanvasObject) -> bool:
    return not canvas_object.visible or CanvasVisualFlag.HIDDEN in canvas_object.visual_state
