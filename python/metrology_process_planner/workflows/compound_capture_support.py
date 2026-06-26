"""Validation and artifact helpers for compound capture workflows."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.artifacts.artifact_ids import artifact_id
from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ProcessOutputRecord,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.workflows.compound_capture_models import (
    CompoundCaptureRequest,
    PendingCompositeCapture,
)


def line_warnings(
    bounds: Box,
    start: Point,
    end: Point,
    metadata: Mapping[str, object],
) -> tuple[str, ...]:
    """Return validation messages for a child line feature."""

    warnings = []
    if start == end:
        warnings.append("Line length must be greater than zero.")
    if not bounds.contains_segment(start, end):
        warnings.append("Line endpoints must be inside the parent site box.")
    target = optional_float(metadata.get("target"))
    lsl = optional_float(metadata.get("lsl"))
    usl = optional_float(metadata.get("usl"))
    if target is not None and lsl is not None and usl is not None and not lsl <= target <= usl:
        warnings.append("Specification limits must satisfy LSL <= target <= USL.")
    return tuple(warnings)


def process_warnings(
    session: SessionRecord,
    capture_id: str,
    request: CompoundCaptureRequest,
) -> tuple[WarningRecord, ...]:
    """Return process warnings for a process-aware capture save."""

    if not process_outputs_enabled(request):
        return ()
    if session.process_context.recipe_id or session.process_context.recipe_path:
        return ()
    return (
        WarningRecord(
            f"warn-{capture_id}-missing-recipe",
            f"{request.mode_id} output was not generated because no process recipe is attached.",
            source="solver",
            code="PROCESS_RECIPE_MISSING",
            related_item_refs=(f"capture:{capture_id}",),
            repair_suggestion="Attach a process recipe and regenerate process outputs.",
        ),
    )


def process_outputs_enabled(request: CompoundCaptureRequest) -> bool:
    """Return whether a compound capture request creates solver-backed outputs."""

    return (
        request.recipe_policy not in {"forbidden", "optional_hidden"}
        or request.solver_operation not in {"", "none"}
        or bool(request.process_artifact_roles)
        or bool(request.process_output_key)
    )


def composite_artifacts(
    capture_id: str,
    image_path: str | None,
    composite: PendingCompositeCapture,
    warning_ids: tuple[str, ...],
) -> tuple[ArtifactRecord, ...]:
    """Return canonical artifacts for a saved composite capture."""

    request = composite.request
    records = []
    if image_path:
        records.append(
            artifact(
                capture_id,
                "site_image",
                "image",
                image_path,
                ArtifactStatus.PRESENT,
                "image/png",
            )
        )
    annotation_role = request.annotation_role
    if not annotation_role:
        raise ValueError(f"Mode {request.mode_id} does not declare an annotation artifact role.")
    records.append(
        artifact(
            capture_id,
            annotation_role,
            "svg",
            f"drawings/{capture_id}-{annotation_role}.svg",
            ArtifactStatus.PLACEHOLDER,
            "image/svg+xml",
            warning_ids,
        )
    )
    for role in request.process_artifact_roles:
        records.append(
            artifact(
                capture_id,
                role,
                "process_output",
                f"process_outputs/{capture_id}-{role}.json",
                ArtifactStatus.PENDING_SOLVER,
                "application/json",
                warning_ids,
            )
        )
    return tuple(records)


def process_output(
    capture_id: str,
    composite: PendingCompositeCapture,
    artifacts: tuple[ArtifactRecord, ...],
    warning_ids: tuple[str, ...],
) -> ProcessOutputRecord:
    """Return a process-output placeholder owned by the saved capture."""

    request = composite.request
    return ProcessOutputRecord(
        f"process-output-{capture_id}",
        f"{request.solver_operation or 'process'} output",
        request.solver_operation or "process_output",
        status="pending_solver",
        artifact_refs={item.owner.role: item.id for item in artifacts},
        metadata={"capture_id": capture_id, "mode_id": request.mode_id},
        warning_ids=warning_ids,
    )


def artifact(
    capture_id: str,
    role: str,
    artifact_type: str,
    path: str,
    status: ArtifactStatus,
    content_type: str,
    warning_ids: tuple[str, ...] = (),
) -> ArtifactRecord:
    """Return a canonical capture-owned artifact."""

    return ArtifactRecord(
        artifact_id("capture", capture_id, role),
        artifact_type,
        role.replace("_", " ").title(),
        path,
        ArtifactOwnerRef("capture", capture_id, role),
        status=status,
        generator="compound_capture",
        file=ArtifactFileMetadata(content_type=content_type),
        repair=ArtifactRepairMetadata(
            "regenerate_process_output",
            "Regenerate process output.",
            regenerable=artifact_type == "process_output",
            requires_recipe=artifact_type == "process_output",
            requires_solver=artifact_type == "process_output",
        ),
        warning_ids=warning_ids,
    )


def optional_float(value: object) -> float | None:
    """Return an optional float from user metadata."""

    if value in {None, ""}:
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean metadata cannot be converted to a number.")
    if isinstance(value, (int, float, str)):
        return float(value)
    raise ValueError(f"Unsupported numeric metadata value: {value!r}")
