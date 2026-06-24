"""Record mutation helpers for process-output regeneration."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.process import SolverResult
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    CaptureRecord,
    ProcessOutputRecord,
)
from metrology_process_planner.workflows.process_capture_extensions import process_solver_request
from metrology_process_planner.workflows.process_regeneration_summary import (
    result_metadata,
    result_summary,
)


def solver_operation(capture: CaptureRecord) -> str:
    """Return the process operation requested by a process-aware capture."""

    request = process_solver_request(capture)
    return str(request.get("operation", "process_output"))


def ready_output(capture: CaptureRecord, result: SolverResult) -> ProcessOutputRecord:
    """Return a ready process output record with solver summary metadata."""

    output = existing_output(capture)
    return ProcessOutputRecord(
        output.id,
        output.label,
        output.output_type,
        status="ready",
        artifact_refs=output.artifact_refs,
        metadata={**dict(output.metadata or {}), **result_metadata(result)},
        extensions={**dict(output.extensions or {}), "solver_result": result_summary(result)},
        warning_ids=(),
    )


def failed_output(capture: CaptureRecord, warning_ids: tuple[str, ...]) -> ProcessOutputRecord:
    """Return a failed process output record."""

    return replace(existing_output(capture), status="failed", warning_ids=warning_ids)


def existing_output(capture: CaptureRecord) -> ProcessOutputRecord:
    """Return the deterministic output record for one process-aware capture."""

    operation = solver_operation(capture)
    return ProcessOutputRecord(
        f"process-output-{capture.id}",
        f"{operation or 'process'} output",
        operation or "process_output",
        status="pending_solver",
        artifact_refs=dict(capture.artifact_refs or {}),
        metadata={"capture_id": capture.id},
    )


def upsert_output(
    outputs: list[ProcessOutputRecord],
    replacement: ProcessOutputRecord,
) -> list[ProcessOutputRecord]:
    """Return outputs with one deterministic record inserted or replaced."""

    replaced = False
    updated = []
    for item in outputs:
        if item.id == replacement.id:
            updated.append(replacement)
            replaced = True
        else:
            updated.append(item)
    if not replaced:
        updated.append(replacement)
    return updated


def mark_output_artifacts(
    artifacts: dict[str, ArtifactRecord],
    capture: CaptureRecord,
    status: ArtifactStatus,
    warning_id: str,
) -> dict[str, ArtifactRecord]:
    """Update process-output artifact records for one capture."""

    refs = set(dict(existing_output(capture).artifact_refs or {}).values())
    for artifact_id, artifact in tuple(artifacts.items()):
        if artifact_id not in refs or artifact.type != "process_output":
            continue
        warning_ids = (warning_id,) if warning_id else ()
        artifacts[artifact_id] = replace(
            artifact,
            status=status,
            warning_ids=warning_ids,
            repair=ArtifactRepairMetadata(
                "regenerate_process_output",
                "Regenerate process output.",
            ),
        )
    return artifacts
