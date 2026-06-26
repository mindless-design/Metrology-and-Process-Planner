"""Process-output artifact lifecycle helpers."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    CaptureRecord,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.workflows.process_output_requests import (
    ProcessOutputRequest,
    SolverInputBuilder,
)
from metrology_process_planner.workflows.process_regeneration_records import (
    existing_output,
    upsert_output,
)


class ProcessOutputService:
    """Create and update process-output records and artifacts."""

    def ensure_ready_artifacts(
        self,
        session: SessionRecord,
        capture: CaptureRecord,
        request: ProcessOutputRequest,
        solver_result_id: str,
    ) -> tuple[dict[str, str], dict[str, ArtifactRecord], tuple[str, ...]]:
        """Return artifact refs and registry updates for a successful solver output."""

        artifacts = dict(session.artifacts or {})
        refs: dict[str, str] = {}
        superseded: list[str] = []
        roles = (*request.output_roles, "process_output_manifest")
        for role in roles:
            record = _output_artifact(
                capture,
                role,
                request,
                ArtifactStatus.STALE,
                (),
                solver_result_id,
            )
            previous = artifacts.get(record.id)
            if previous is not None and previous.status == ArtifactStatus.PRESENT:
                artifacts[previous.id] = replace(previous, status=ArtifactStatus.SUPERSEDED)
                superseded.append(previous.id)
            artifacts[record.id] = record
            refs[role] = record.id
        return refs, artifacts, tuple(superseded)

    def ensure_placeholder_outputs(
        self,
        session: SessionRecord,
        captures: tuple[CaptureRecord, ...],
        warnings: tuple[WarningRecord, ...],
    ) -> SessionRecord:
        """Ensure warning-only process outputs have deliberate placeholder artifacts."""

        outputs = list(session.process_outputs)
        artifacts = dict(session.artifacts or {})
        warning_ids = tuple(warning.id for warning in warnings)
        builder = SolverInputBuilder()
        for capture in captures:
            request = builder.build_request(session, capture)
            refs = dict(existing_output(capture).artifact_refs or {})
            for artifact in self.placeholder_artifacts(capture, request, warning_ids):
                artifacts[artifact.id] = artifact
                refs[artifact.owner.role] = artifact.id
            output = replace(
                existing_output(capture),
                status="pending_solver",
                artifact_refs=refs,
                warning_ids=warning_ids,
                metadata={
                    **dict(existing_output(capture).metadata or {}),
                    "solver_operation": request.operation,
                    "render_profile": request.render_profile,
                },
            )
            outputs = upsert_output(outputs, output)
        return replace(session, process_outputs=tuple(outputs), artifacts=artifacts)

    def placeholder_artifacts(
        self,
        capture: CaptureRecord,
        request: ProcessOutputRequest,
        warning_ids: tuple[str, ...],
    ) -> tuple[ArtifactRecord, ...]:
        """Return placeholder artifacts for a process-output request."""

        roles = (*request.output_roles, "process_output_manifest")
        return tuple(_placeholder_artifact(capture, role, request, warning_ids) for role in roles)


def _placeholder_artifact(
    capture: CaptureRecord,
    role: str,
    request: ProcessOutputRequest,
    warning_ids: tuple[str, ...],
) -> ArtifactRecord:
    return _output_artifact(capture, role, request, ArtifactStatus.PLACEHOLDER, warning_ids, "")


def _output_artifact(
    capture: CaptureRecord,
    role: str,
    request: ProcessOutputRequest,
    status: ArtifactStatus,
    warning_ids: tuple[str, ...],
    solver_result_id: str,
) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id("capture", capture.id, role),
        "process_output",
        role.replace("_", " ").title(),
        f"process_outputs/{capture.id}-{role}.json",
        ArtifactOwnerRef("capture", capture.id, role),
        status=status,
        generator="process_output_service",
        file=ArtifactFileMetadata(content_type="application/json"),
        repair=ArtifactRepairMetadata(
            "regenerate_process_output",
            "Regenerate process output.",
            regenerable=True,
            requires_recipe=True,
            requires_solver=True,
        ),
        warning_ids=warning_ids,
        dependencies=(),
        extensions={
            "artifact_type": role,
            "solver_operation": request.operation,
            "render_profile": request.render_profile,
            "render_profile_id": request.render_profile,
            "solver_result_id": solver_result_id,
            "process_context_ref": "process_context.active",
            "geometry_kind": request.geometry_kind,
        },
    )
