"""Artifact repair service and command routing."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.generators import (
    ArtifactGenerator,
    ArtifactGeneratorRegistry,
    built_in_generator_registry,
)
from metrology_process_planner.workflows.artifacts.layout_crop_generator import LayoutImageExporter
from metrology_process_planner.workflows.artifacts.relink import relink_artifact_record
from metrology_process_planner.workflows.artifacts.repair_bulk import repair_all_with_status
from metrology_process_planner.workflows.artifacts.repair_generation import (
    call_handler,
    generation_result,
)
from metrology_process_planner.workflows.artifacts.repair_operations import (
    repair_candidate_artifacts,
    repair_request_with_generator,
    with_ignored_warning,
)
from metrology_process_planner.workflows.artifacts.repair_support import (
    is_process_only_repair_artifact,
    with_failed_generation,
    with_unavailable,
)
from metrology_process_planner.workflows.artifacts.requests import (
    RepairRequest,
    RepairRequestStatus,
)
from metrology_process_planner.workflows.artifacts.scan_result import ArtifactScanResult
from metrology_process_planner.workflows.artifacts.scanner import ArtifactScanner


class ArtifactRepairService:
    """Route artifact lifecycle repairs through registered generators."""

    def __init__(
        self,
        scanner: ArtifactScanner | None = None,
        generators: ArtifactGeneratorRegistry | None = None,
        layout_view: LayoutImageExporter | None = None,
    ) -> None:
        self._scanner = scanner if scanner is not None else ArtifactScanner()
        self._generators = generators if generators is not None else built_in_generator_registry()
        if layout_view is not None:
            from metrology_process_planner.workflows.artifacts.generator_builtins import (
                layout_crop_registration,
            )

            self._generators.register(layout_crop_registration(layout_view))

    def scan_session(
        self,
        session: SessionRecord,
        paths: SessionPaths | Path | str,
        mode_registry: ModeRegistry | None = None,
    ) -> tuple[SessionRecord, ArtifactScanResult]:
        """Scan artifact health and return the scanner result."""

        return self._scanner.scan_session(session, paths, mode_registry)

    def build_repair_requests(
        self,
        session: SessionRecord,
        mode_registry: ModeRegistry | None = None,
    ) -> tuple[RepairRequest, ...]:
        """Build repair requests for currently actionable artifact problems."""

        return tuple(
            self._request_for(session, artifact)
            for artifact in repair_candidate_artifacts(session, mode_registry)
        )

    def can_repair(self, session: SessionRecord, artifact_id: str) -> bool:
        """Return whether an artifact has an available repair path now."""

        artifact = (session.artifacts or {}).get(artifact_id)
        if artifact is None:
            return False
        return self._request_for(session, artifact).status is RepairRequestStatus.AVAILABLE

    def repair_artifact(
        self,
        session: SessionRecord,
        artifact_id: str,
        paths: SessionPaths,
        mode_registry: ModeRegistry | None = None,
    ) -> SessionRecord:
        """Regenerate one artifact or store a structured unavailable warning."""

        artifact = (session.artifacts or {}).get(artifact_id)
        if artifact is None:
            return session
        if is_process_only_repair_artifact(session, artifact, mode_registry):
            return session
        request = self._request_for(session, artifact)
        if request.status is not RepairRequestStatus.AVAILABLE:
            return with_unavailable(session, artifact, request)
        registration = self._generators.generator_for(artifact)
        if registration is None or registration.handler is None:
            return with_unavailable(session, artifact, request)
        return _repair_with_handler(
            session,
            artifact,
            paths,
            registration.handler,
            mode_registry,
        )

    def repair_all_missing(
        self,
        session: SessionRecord,
        paths: SessionPaths,
        mode_registry: ModeRegistry | None = None,
    ) -> SessionRecord:
        """Repair every missing artifact with an available generator."""

        return repair_all_with_status(
            session,
            paths,
            ArtifactStatus.MISSING,
            self.repair_artifact,
            mode_registry,
        )

    def repair_all_stale(
        self,
        session: SessionRecord,
        paths: SessionPaths,
        mode_registry: ModeRegistry | None = None,
    ) -> SessionRecord:
        """Repair every stale artifact with an available generator."""

        return repair_all_with_status(
            session,
            paths,
            ArtifactStatus.STALE,
            self.repair_artifact,
            mode_registry,
        )

    def relink_artifact(
        self,
        session: SessionRecord,
        artifact_id: str,
        relative_path: str,
        mode_registry: ModeRegistry | None = None,
    ) -> SessionRecord:
        """Update a managed artifact path and clear missing-warning state."""

        artifact = (session.artifacts or {}).get(artifact_id)
        if artifact is None or is_process_only_repair_artifact(
            session,
            artifact,
            mode_registry,
        ):
            return session
        return relink_artifact_record(session, artifact_id, relative_path)

    def mark_ignored(self, session: SessionRecord, warning_id_value: str) -> SessionRecord:
        """Mark one artifact warning as intentionally ignored."""

        return with_ignored_warning(session, warning_id_value)

    def _request_for(self, session: SessionRecord, artifact: ArtifactRecord) -> RepairRequest:
        return repair_request_with_generator(session, artifact, self._generators)


def _repair_with_handler(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
    handler: ArtifactGenerator,
    mode_registry: ModeRegistry | None = None,
) -> SessionRecord:
    try:
        generated = call_handler(session, artifact, paths, handler, mode_registry)
    except Exception as exc:  # noqa: BLE001 - failed generators are captured as diagnostics.
        return with_failed_generation(session, artifact, str(exc))
    generated_session, repaired = generation_result(session, generated)
    artifacts = dict(session.artifacts or {})
    if generated_session is not session:
        artifacts = dict(generated_session.artifacts or {})
    artifacts[artifact.id] = repaired
    return replace(generated_session, artifacts=artifacts)

