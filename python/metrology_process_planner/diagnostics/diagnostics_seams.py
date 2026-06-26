"""Pure seam checkers for session, editor, canvas, and filesystem state."""

from __future__ import annotations

from metrology_process_planner.diagnostics.diagnostics_models import DiffResult
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.workflows.editor.document import SessionDocument


def check_pending_to_saved_seam(
    before: SessionRecord,
    after: SessionRecord,
    pending_id: str,
) -> DiffResult:
    """Check that a pending capture was promoted into saved session state."""

    saved_ids = _new_capture_ids(before, after)
    return _diff(
        missing=_pending_save_missing(saved_ids, after),
        mismatched=_pending_save_mismatches(after, pending_id),
    )


def check_session_to_editor_seam(document: SessionDocument) -> DiffResult:
    """Check that session records are represented in the editor document."""

    return _diff(
        missing=_missing_capture_items(document) + _missing_pending_items(document),
    )


def check_session_to_filesystem_seam(
    session: SessionRecord,
    paths: SessionPaths,
) -> DiffResult:
    """Check that registered artifact files exist or are covered by warnings."""

    warning_paths = {warning.artifact_path for warning in session.warnings if warning.artifact_path}
    missing = _missing_artifact_paths(session, paths, warning_paths)
    return _diff(
        missing=tuple(missing),
        suggested_repairs=("Regenerate missing artifacts or attach a WarningRecord.",)
        if missing
        else (),
    )


def check_editor_canvas_selection_seam(document: SessionDocument) -> DiffResult:
    """Check that editor selection and canvas-object indexes agree."""

    selected = document.selection.selected_item_id
    if selected not in document.items_by_id:
        return _diff(missing=(f"Selected SessionItem {selected} is missing.",))
    item = document.items_by_id[selected]
    expected = set(item.canvas_object_ids)
    actual = set(document.selection.selected_canvas_object_ids)
    mismatched: tuple[str, ...] = ()
    if expected != actual:
        mismatched = (f"Selected item canvas ids {expected} do not match {actual}.",)
    return _diff(mismatched=mismatched)


def _artifact_paths(session: SessionRecord) -> tuple[str, ...]:
    return tuple(artifact.relative_path for artifact in (session.artifacts or {}).values())


def _new_capture_ids(before: SessionRecord, after: SessionRecord) -> set[str]:
    before_ids = {capture.id for capture in before.captures}
    return {capture.id for capture in after.captures if capture.id not in before_ids}


def _pending_save_missing(saved_ids: set[str], after: SessionRecord) -> tuple[str, ...]:
    missing: list[str] = []
    if not saved_ids:
        missing.append("No new CaptureRecord was created.")
    if not any(obj.record_id in saved_ids for obj in after.canvas_objects):
        missing.append("No CanvasObject points at the promoted CaptureRecord.")
    return tuple(missing)


def _pending_save_mismatches(after: SessionRecord, pending_id: str) -> tuple[str, ...]:
    if any(item.id == pending_id for item in after.pending_captures):
        return (f"PendingCapture {pending_id} still exists after save.",)
    return ()


def _missing_capture_items(document: SessionDocument) -> tuple[str, ...]:
    missing: list[str] = []
    for capture in document.session.captures:
        if f"capture:{capture.id}" not in document.items_by_id:
            missing.append(f"Missing SessionItem for capture {capture.id}.")
        missing.extend(
            f"Missing SessionItem for measurement {measurement.id}."
            for measurement in capture.measurements
            if f"measurement:{measurement.id}" not in document.items_by_id
        )
    return tuple(missing)


def _missing_pending_items(document: SessionDocument) -> tuple[str, ...]:
    return tuple(
        f"Missing SessionItem for pending capture {pending.id}."
        for pending in document.session.pending_captures
        if f"pending:{pending.id}" not in document.items_by_id
    )


def _missing_artifact_paths(
    session: SessionRecord,
    paths: SessionPaths,
    warning_paths: set[str],
) -> tuple[str, ...]:
    return tuple(
        artifact_path
        for artifact_path in _artifact_paths(session)
        if artifact_path not in warning_paths
        and not artifact_path_to_disk(paths.folder, artifact_path).exists()
    )


def _diff(
    missing: tuple[str, ...] | list[str] = (),
    extra: tuple[str, ...] | list[str] = (),
    mismatched: tuple[str, ...] | list[str] = (),
    warnings: tuple[str, ...] | list[str] = (),
    suggested_repairs: tuple[str, ...] | list[str] = (),
) -> DiffResult:
    return DiffResult(
        ok=not missing and not extra and not mismatched,
        missing=tuple(missing),
        extra=tuple(extra),
        mismatched=tuple(mismatched),
        warnings=tuple(warnings),
        suggested_repairs=tuple(suggested_repairs),
    )
