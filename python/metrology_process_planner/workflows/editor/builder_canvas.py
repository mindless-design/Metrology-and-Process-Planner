"""Canvas-object indexes for editor document items."""

from __future__ import annotations

from metrology_process_planner.domains.session import SessionRecord


def pending_canvas_ids(session: SessionRecord, parent_canvas_id: str) -> tuple[str, ...]:
    """Return parent and child canvas ids for a pending capture."""

    return tuple(
        item.id
        for item in session.canvas_objects
        if item.id == parent_canvas_id or item.parent_id == parent_canvas_id
    )


def capture_canvas_ids(session: SessionRecord, capture_id: str) -> tuple[str, ...]:
    """Return parent and child canvas ids for a saved capture."""

    parent_ids = tuple(
        item.id for item in session.canvas_objects if item.record_id == capture_id
    )
    return parent_ids + tuple(
        item.id
        for item in session.canvas_objects
        if item.parent_id in parent_ids and item.id not in parent_ids
    )
