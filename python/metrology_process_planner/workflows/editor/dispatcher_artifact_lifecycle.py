"""Artifact lifecycle actions for direct editor workflow dispatch."""

from __future__ import annotations

import json
from typing import Optional, Protocol

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction


class _ArtifactLifecycleDispatcher(Protocol):
    """Dispatcher fields needed by artifact lifecycle actions."""

    _paths: Optional[SessionPaths]
    _mode_registry: ModeRegistry | None

    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after workflow state changes."""


def scan_artifacts_action(
    dispatcher: _ArtifactLifecycleDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Scan session artifacts and rebuild the editor document."""

    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    session, result = ArtifactRepairService().scan_session(
        document.session,
        dispatcher._paths,
        dispatcher._mode_registry,
    )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        f"Scanned {result.artifact_count} artifacts; {result.missing_count} missing.",
    )


def regenerate_missing_artifacts_action(
    dispatcher: _ArtifactLifecycleDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Scan and repair visible missing artifacts."""

    return _repair_all(dispatcher, document, missing=True)


def regenerate_stale_artifacts_action(
    dispatcher: _ArtifactLifecycleDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Scan and repair visible stale artifacts."""

    return _repair_all(dispatcher, document, missing=False)


def export_artifact_manifest_action(
    dispatcher: _ArtifactLifecycleDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Export the visible artifact registry as JSON."""

    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    destination = dispatcher._paths.folder / "artifact_manifest.json"
    payload = {
        artifact_id: artifact.to_dict()
        for artifact_id, artifact in sorted((document.session.artifacts or {}).items())
        if artifact_visible_for_session(document.session, artifact, dispatcher._mode_registry)
    }
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return EditorActionResult(
        "success",
        document,
        "Artifact manifest exported.",
        destination,
    )


def _repair_all(
    dispatcher: _ArtifactLifecycleDispatcher,
    document: SessionDocument,
    *,
    missing: bool,
) -> EditorActionResult:
    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    service = ArtifactRepairService()
    scanned, _scan_result = service.scan_session(
        document.session,
        dispatcher._paths,
        dispatcher._mode_registry,
    )
    candidate_count = _candidate_count(scanned, missing, dispatcher._mode_registry)
    session = (
        service.repair_all_missing(scanned, dispatcher._paths, dispatcher._mode_registry)
        if missing
        else service.repair_all_stale(scanned, dispatcher._paths, dispatcher._mode_registry)
    )
    blocked = len(service.build_repair_requests(session, dispatcher._mode_registry))
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        f"Artifact repair queue processed: {candidate_count} candidate(s), {blocked} blocked.",
    )


def _candidate_count(
    session: SessionRecord,
    missing: bool,
    mode_registry: ModeRegistry | None,
) -> int:
    status = "missing" if missing else "stale"
    return sum(
        1
        for artifact in (session.artifacts or {}).values()
        if artifact.status.value == status
        and artifact_visible_for_session(session, artifact, mode_registry)
    )
