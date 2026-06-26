"""Warning action dispatch helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    SessionRecord,
    utc_now_iso,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


class _DocumentRebuilder(Protocol):
    """Editor dispatcher capability needed after warning changes."""

    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after a workflow mutation."""


def ignore_warning_action(
    dispatcher: _DocumentRebuilder,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Mark one warning ignored without deleting canonical warning history."""

    warning_id = _warning_id(document, action)
    if not warning_id:
        return EditorActionResult("unavailable", document, "No warning was selected.")
    changed = False
    warnings = []
    for warning in document.session.warnings:
        if warning.id == warning_id:
            changed = True
            warnings.append(replace(warning, status="ignored", resolved_at=utc_now_iso()))
        else:
            warnings.append(warning)
    if not changed:
        return EditorActionResult("unavailable", document, "Warning no longer exists.")
    session = replace(
        document.session,
        artifacts=_ignored_artifacts(document.session, warning_id),
        warnings=tuple(warnings),
    )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Warning ignored.",
    )


def warning_action_result(
    dispatcher: _DocumentRebuilder,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult | None:
    """Dispatch warning-related editor actions when the action matches."""

    if action.action_type is EditorActionType.IGNORE_WARNING:
        return ignore_warning_action(dispatcher, document, action)
    if action.action_type is EditorActionType.OPEN_RECIPE_FILE:
        return open_recipe_file_action(document, action)
    return None


def open_recipe_file_action(document: SessionDocument, action: EditorAction) -> EditorActionResult:
    """Return a typed recipe-path handoff for the UI shell."""

    recipe_path = dict(action.payload).get("recipe_path", "")
    if not recipe_path:
        return EditorActionResult("unavailable", document, "No recipe path was provided.")
    path = Path(recipe_path)
    if not path.exists():
        return EditorActionResult(
            "unavailable",
            document,
            f"Recipe file does not exist: {recipe_path}",
        )
    return EditorActionResult(
        "success",
        document,
        "Recipe file is ready to open.",
        path,
    )


def _warning_id(document: SessionDocument, action: EditorAction) -> str:
    item = document.items_by_id.get(action.item_id)
    if item is None:
        return action.item_id.removeprefix("warning:")
    if item.record_ref is not None and item.record_ref.record_type == "warning":
        return item.record_ref.record_id
    return item.warning_ids[0] if item.warning_ids else ""


def _ignored_artifacts(
    session: SessionRecord,
    warning_id: str,
) -> Mapping[str, ArtifactRecord] | None:
    warning = next((item for item in session.warnings if item.id == warning_id), None)
    if warning is None or warning.source != "artifact":
        return session.artifacts
    artifact_ids = set(warning.related_artifact_refs)
    return {
        artifact_id: replace(artifact, status=ArtifactStatus.INTENTIONALLY_IGNORED)
        if artifact_id in artifact_ids
        else artifact
        for artifact_id, artifact in (session.artifacts or {}).items()
    }
