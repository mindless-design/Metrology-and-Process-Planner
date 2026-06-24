"""Compact JSON-serializable state snapshots for seam tracing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from metrology_process_planner import __version__
from metrology_process_planner.domains.session import CanvasObject, SessionRecord
from metrology_process_planner.infrastructure.diagnostics_models import (
    DiagnosticEvent,
    DiagnosticsSnapshot,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.canvas_interaction_models import InteractionContext
from metrology_process_planner.workflows.editor.document import SessionDocument


def build_diagnostics_snapshot(
    package_root: Path,
    events: tuple[DiagnosticEvent, ...] = (),
) -> DiagnosticsSnapshot:
    """Build a diagnostics snapshot from package paths and events."""

    root = package_root.resolve()
    return DiagnosticsSnapshot(
        plugin_version=__version__,
        package_root=str(root),
        python_root=str(root / "python"),
        events=events,
    )


def snapshot_workflow_state(context: InteractionContext) -> dict[str, Any]:
    """Return a compact summary of runtime interaction state."""

    return {
        "armed_object_type": context.armed_object_type.value
        if context.armed_object_type is not None
        else "",
        "active_parent_id": context.active_parent_id,
        "live_preview_id": context.live_preview_id,
        "drag_start": context.drag_start.to_dict() if context.drag_start is not None else None,
    }


def snapshot_session_document(document: SessionDocument) -> dict[str, Any]:
    """Return a compact summary of an editor document."""

    session = document.session
    return {
        "session_id": session.id,
        "mode_id": session.mode.value,
        "capture_count": len(session.captures),
        "pending_count": len(session.pending_captures),
        "measurement_count": sum(len(capture.measurements) for capture in session.captures),
        "artifact_count": len(session.artifacts or {}),
        "warning_count": len(session.warnings),
        "dirty": document.dirty_state.is_dirty,
        "item_count": len(document.items_by_id),
        "selected_item_id": document.selection.selected_item_id,
    }


def snapshot_canvas_objects(session: SessionRecord) -> tuple[dict[str, Any], ...]:
    """Return compact summaries for all canvas objects."""

    return tuple(_canvas_object_snapshot(item) for item in session.canvas_objects)


def snapshot_artifact_manifest(session: SessionRecord) -> dict[str, Any]:
    """Return all session artifact paths grouped by owner."""

    grouped: dict[str, list[str]] = {}
    for artifact in (session.artifacts or {}).values():
        key = f"{artifact.owner.owner_type}:{artifact.owner.owner_id}"
        grouped.setdefault(key, []).append(artifact.relative_path)
    return {key: sorted(paths) for key, paths in sorted(grouped.items())}


def snapshot_filesystem_artifacts(paths: SessionPaths) -> dict[str, Any]:
    """Return a compact listing of files in managed artifact folders."""

    return {
        "images": _relative_files(paths.folder, paths.images_dir),
        "drawings": _relative_files(paths.folder, paths.drawings_dir),
        "reports": _relative_files(paths.folder, paths.reports_dir),
        "session_json_exists": paths.session_json.exists(),
        "capture_csv_exists": paths.capture_csv.exists(),
    }


def snapshot_overlay_manager(commands: Any = None) -> dict[str, Any]:
    """Return a compact summary of overlay-manager visible commands/state."""

    items = tuple(commands or ())
    return {
        "command_count": len(items),
        "visible_object_ids": [
            getattr(command, "object_id", "")
            for command in items
            if getattr(command, "object_id", "")
        ],
    }


def snapshot_editor_view_model(document: SessionDocument) -> dict[str, Any]:
    """Return a compact summary of editor view state."""

    return {
        "selected_item_id": document.selection.selected_item_id,
        "selected_canvas_object_ids": list(document.selection.selected_canvas_object_ids),
        "group_count": len(document.navigator_groups),
        "warning_count": len(document.warning_view_models),
    }


def snapshot_report_model(report_model: Any = None) -> dict[str, Any]:
    """Return a compact summary of a report model when one is available."""

    if report_model is None:
        return {"available": False}
    return {
        "available": True,
        "export_count": len(getattr(report_model, "exports", ())),
        "warning_count": len(getattr(report_model, "warnings", ())),
    }


def _canvas_object_snapshot(canvas_object: CanvasObject) -> dict[str, Any]:
    bounds = canvas_object.geometry.bounds
    return {
        "id": canvas_object.id,
        "type": canvas_object.object_type.value,
        "parent_id": canvas_object.parent_id,
        "record_id": canvas_object.record_id,
        "visual_state": [flag.value for flag in canvas_object.visual_state],
        "geometry_hash": hash(str(canvas_object.geometry.to_dict())),
        "visible": canvas_object.visible,
        "selected": any(flag.value == "selected" for flag in canvas_object.visual_state),
        "stale": canvas_object.stale,
        "warning_count": len(canvas_object.warning_ids),
        "bounds": bounds.to_dict() if bounds is not None else None,
    }


def _relative_files(root: Path, folder: Path) -> list[str]:
    if not folder.exists():
        return []
    return [
        str(path.relative_to(root)).replace("\\", "/")
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    ]
