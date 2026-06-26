"""Artifact command operation helpers for the session editor."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_editor_command_results import no_document
from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.document import SessionDocument

DocumentUpdater = Callable[[SessionDocument], None]


def export_artifact_manifest_command(
    document: SessionDocument | None,
    paths: SessionPaths | None,
    mode_registry: ModeRegistry | None,
) -> CommandRouteResult:
    """Export the current canonical artifact registry as JSON."""

    if document is None:
        return no_document(CommandId.EXPORT_ARTIFACT_MANIFEST, "exporting artifacts")
    if paths is None:
        return _unavailable(CommandId.EXPORT_ARTIFACT_MANIFEST, "No session folder is available.")
    destination = paths.folder / "artifact_manifest.json"
    payload = {
        artifact_id: artifact.to_dict()
        for artifact_id, artifact in sorted((document.session.artifacts or {}).items())
        if artifact_visible_for_session(document.session, artifact, mode_registry)
    }
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return CommandRouteResult(
        CommandId.EXPORT_ARTIFACT_MANIFEST,
        "success",
        "Artifact manifest exported.",
        output_path=str(destination),
    )


def repair_all_command(
    command_id: CommandId,
    document: SessionDocument | None,
    paths: SessionPaths | None,
    mode_registry: ModeRegistry | None,
    service: ArtifactRepairService,
    missing: bool,
    update_document: DocumentUpdater,
) -> CommandRouteResult:
    """Run a missing or stale artifact repair queue and refresh the editor."""

    if document is None:
        return no_document(command_id, "repairing artifacts")
    if paths is None:
        return _unavailable(command_id, "No session folder is available.")
    session, candidates = _repair_queue(service, document.session, paths, missing, mode_registry)
    blocked = len(service.build_repair_requests(session, mode_registry))
    update_document(rebuilt_document(session, document, mode_registry))
    return CommandRouteResult(
        command_id,
        "success",
        f"Artifact repair queue processed: {candidates} candidate(s), {blocked} blocked.",
    )


def _repair_queue(
    service: ArtifactRepairService,
    session: SessionRecord,
    paths: SessionPaths,
    missing: bool,
    mode_registry: ModeRegistry | None = None,
) -> tuple[SessionRecord, int]:
    scanned, _scan_result = service.scan_session(session, paths, mode_registry)
    repaired = (
        service.repair_all_missing(scanned, paths, mode_registry)
        if missing
        else service.repair_all_stale(scanned, paths, mode_registry)
    )
    return repaired, _candidate_count(scanned, missing, mode_registry)


def _candidate_count(
    session: SessionRecord,
    missing: bool,
    mode_registry: ModeRegistry | None = None,
) -> int:
    status = "missing" if missing else "stale"
    return sum(
        1
        for artifact in (session.artifacts or {}).values()
        if artifact.status.value == status
        and artifact_visible_for_session(session, artifact, mode_registry)
    )


def _unavailable(command_id: CommandId, message: str) -> CommandRouteResult:
    return CommandRouteResult(command_id, "unavailable", message)


def rebuilt_document(
    session: SessionRecord,
    previous: SessionDocument,
    mode_registry: ModeRegistry | None = None,
) -> SessionDocument:
    """Rebuild an editor document while preserving selection when possible."""

    document = SessionDocumentBuilder(mode_registry=mode_registry).build(session)
    if previous.selection.selected_item_id in document.items_by_id:
        return replace(document, selection=previous.selection)
    return document
