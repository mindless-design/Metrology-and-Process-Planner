"""Pure helpers for updating persistent canvas object state."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from metrology_process_planner.domains.session import (
    CanvasObject,
    CanvasVisualFlag,
    SessionRecord,
)


def find_canvas_object(session: SessionRecord, object_id: str) -> Optional[CanvasObject]:
    """Return a canvas object by id when it exists."""

    for canvas_object in session.canvas_objects:
        if canvas_object.id == object_id:
            return canvas_object
    return None


def replace_canvas_object(
    session: SessionRecord,
    replacement: CanvasObject,
) -> SessionRecord:
    """Return a session with one canvas object replaced or appended."""

    objects = []
    replaced = False
    for canvas_object in session.canvas_objects:
        if canvas_object.id == replacement.id:
            objects.append(replacement)
            replaced = True
        else:
            objects.append(canvas_object)
    if not replaced:
        objects.append(replacement)
    return replace(session, canvas_objects=tuple(objects))


def remove_canvas_object(session: SessionRecord, object_id: str) -> SessionRecord:
    """Return a session without the requested canvas object."""

    return replace(
        session,
        canvas_objects=tuple(item for item in session.canvas_objects if item.id != object_id),
    )


def select_canvas_object(session: SessionRecord, object_id: str) -> SessionRecord:
    """Return a session where one selectable object is visually selected."""

    objects = []
    for canvas_object in session.canvas_objects:
        flags = _without_flag(canvas_object.visual_state, CanvasVisualFlag.SELECTED)
        if canvas_object.id == object_id and canvas_object.selectable:
            flags = _with_flag(flags, CanvasVisualFlag.SELECTED)
        objects.append(replace(canvas_object, visual_state=flags))
    return replace(session, canvas_objects=tuple(objects))


def set_active_parent_object(session: SessionRecord, object_id: Optional[str]) -> SessionRecord:
    """Return a session where one object is marked as the active parent."""

    objects = []
    for canvas_object in session.canvas_objects:
        flags = _without_flag(canvas_object.visual_state, CanvasVisualFlag.ACTIVE_PARENT)
        if canvas_object.id == object_id:
            flags = _with_flag(flags, CanvasVisualFlag.ACTIVE_PARENT)
        objects.append(replace(canvas_object, visual_state=flags))
    return replace(session, canvas_objects=tuple(objects))


def _with_flag(
    flags: tuple[CanvasVisualFlag, ...],
    flag: CanvasVisualFlag,
) -> tuple[CanvasVisualFlag, ...]:
    if flag in flags:
        return flags
    return flags + (flag,)


def _without_flag(
    flags: tuple[CanvasVisualFlag, ...],
    flag: CanvasVisualFlag,
) -> tuple[CanvasVisualFlag, ...]:
    return tuple(item for item in flags if item is not flag)
