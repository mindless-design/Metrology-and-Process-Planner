"""Named diff helpers for diagnostics seam comparisons."""

from __future__ import annotations

from metrology_process_planner.infrastructure.diagnostics_models import DiffResult
from metrology_process_planner.infrastructure.diagnostics_seams import (
    check_editor_canvas_selection_seam,
    check_session_to_editor_seam,
    check_session_to_filesystem_seam,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.document import SessionDocument


def diff_session_vs_editor(document: SessionDocument, _editor_model: object = None) -> DiffResult:
    """Compare canonical session data with editor document items."""

    return check_session_to_editor_seam(document)


def diff_session_vs_canvas(document: SessionDocument, overlay_manager: object = None) -> DiffResult:
    """Compare selected session/editor canvas state."""

    return check_editor_canvas_selection_seam(document)


def diff_session_vs_filesystem(document: SessionDocument, paths: SessionPaths) -> DiffResult:
    """Compare session artifact refs with files on disk."""

    return check_session_to_filesystem_seam(document.session, paths)


def diff_manifest_vs_filesystem(manifest: dict[str, object], paths: SessionPaths) -> DiffResult:
    """Compare a simple artifact manifest with files on disk."""

    expected = _manifest_paths(manifest)
    missing = tuple(path for path in expected if not (paths.folder / path).exists())
    return DiffResult(ok=not missing, missing=missing)


def diff_parent_child_integrity(document: SessionDocument) -> DiffResult:
    """Check editor parent/child links resolve both directions."""

    missing = []
    for item in document.items_by_id.values():
        if item.parent_id and item.parent_id not in document.items_by_id:
            missing.append(f"{item.item_id} parent {item.parent_id}")
        for child_id in item.child_ids:
            child = document.items_by_id.get(child_id)
            if child is None or child.parent_id != item.item_id:
                missing.append(f"{item.item_id} child {child_id}")
    return DiffResult(ok=not missing, missing=tuple(missing))


def diff_pending_state(
    workflow_state: object,
    document: SessionDocument,
    _editor_model: object = None,
) -> DiffResult:
    """Compare pending workflow state with editor pending items."""

    pending_ids = {f"pending:{pending.id}" for pending in document.session.pending_captures}
    item_ids = set(document.items_by_id)
    missing = tuple(sorted(pending_ids.difference(item_ids)))
    return DiffResult(ok=not missing, missing=missing)


def _manifest_paths(manifest: dict[str, object]) -> tuple[str, ...]:
    paths: list[str] = []
    for value in manifest.values():
        if isinstance(value, dict):
            paths.extend(path for items in value.values() for path in items)
        elif isinstance(value, list):
            paths.extend(str(item) for item in value)
    return tuple(paths)
