"""Small parsing helpers for canonical session serialization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metrology_process_planner.domains.session.artifact_registry import ArtifactRecord
from metrology_process_planner.domains.session.canvas import CanvasObject, PendingCapture


def artifact_records(data: object) -> dict[str, ArtifactRecord]:
    """Build artifact records from the canonical registry mapping."""

    if not isinstance(data, Mapping):
        return {}
    return {
        str(key): ArtifactRecord.from_dict(value)
        for key, value in dict(data).items()
        if isinstance(value, Mapping)
    }


def canvas_objects_from_extensions(data: Mapping[str, Any]) -> tuple[CanvasObject, ...]:
    """Build persistent canvas objects from the canvas extension block."""

    return tuple(CanvasObject.from_dict(item) for item in _extension_items(data, "canvas_objects"))


def pending_captures_from_extensions(data: Mapping[str, Any]) -> tuple[PendingCapture, ...]:
    """Build pending captures from the canvas extension block."""

    return tuple(
        PendingCapture.from_dict(item) for item in _extension_items(data, "pending_captures")
    )


def _extension_items(data: Mapping[str, Any], item_key: str) -> tuple[Mapping[str, Any], ...]:
    extensions = data.get("extensions", {})
    if not isinstance(extensions, Mapping):
        return ()
    canvas = extensions.get("canvas", {})
    if not isinstance(canvas, Mapping):
        return ()
    items = canvas.get(item_key, ())
    if not isinstance(items, list):
        return ()
    return tuple(item for item in items if isinstance(item, Mapping))
