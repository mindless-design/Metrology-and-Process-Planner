"""Reporting Workbench adapter for artifact repair services."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.document import SessionDocument


class ReportingWorkbenchArtifactRepairService:
    """Repair report artifacts through the canonical artifact repair service."""

    def __init__(
        self,
        repair_service: ArtifactRepairService | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._repair_service = repair_service or ArtifactRepairService()
        self._mode_registry = mode_registry

    def regenerate_missing(
        self,
        document: SessionDocument,
        paths: SessionPaths,
    ) -> SessionDocument:
        """Return a refreshed document after regenerating missing artifacts."""

        scanned, _result = self._repair_service.scan_session(
            document.session,
            paths,
            self._mode_registry,
        )
        session = self._repair_service.repair_all_missing(
            scanned,
            paths,
            self._mode_registry,
        )
        return _rebuilt(document, session, self._mode_registry)

    def regenerate_stale(
        self,
        document: SessionDocument,
        paths: SessionPaths,
    ) -> SessionDocument:
        """Return a refreshed document after regenerating stale artifacts."""

        scanned, _result = self._repair_service.scan_session(
            document.session,
            paths,
            self._mode_registry,
        )
        session = self._repair_service.repair_all_stale(
            scanned,
            paths,
            self._mode_registry,
        )
        return _rebuilt(document, session, self._mode_registry)


def _rebuilt(
    previous: SessionDocument,
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> SessionDocument:
    document = SessionDocumentBuilder(mode_registry=mode_registry).build(session)
    return replace(
        document,
        loaded_path=previous.loaded_path,
        revision=previous.revision,
        selection=previous.selection,
        dirty_state=previous.dirty_state,
    )
