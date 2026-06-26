"""Artifact-specific Advanced Diagnostics action helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from metrology_process_planner.app import diagnostics_summary as diag_summary
from metrology_process_planner.app.diagnostics_action_results import DiagnosticsActionResult
from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.workflows.artifacts import (
    ArtifactRepairService,
    ArtifactScanResult,
    built_in_generator_registry,
)

if TYPE_CHECKING:
    from metrology_process_planner.app.diagnostics_action_dispatch import DiagnosticsActionContext


def scan_artifacts(
    action_id: str,
    context: DiagnosticsActionContext,
) -> DiagnosticsActionResult:
    """Run an artifact scan for diagnostics."""

    if context.paths is None:
        return DiagnosticsActionResult(
            action_id,
            "unavailable",
            "No session folder is available for artifact scanning.",
        )
    _session, result = ArtifactRepairService().scan_session(
        context.session,
        context.paths,
        context.mode_registry,
    )
    message = (
        f"Scanned {result.artifact_count} artifact records; "
        f"{result.missing_count} missing; {result.stale_count} stale."
    )
    return DiagnosticsActionResult(action_id, "success", message, artifact_health_text(result))


def copy_repair_queue(
    action_id: str,
    context: DiagnosticsActionContext,
) -> DiagnosticsActionResult:
    """Prepare repair queue text for diagnostics."""

    requests = ArtifactRepairService().build_repair_requests(
        context.session,
        context.mode_registry,
    )
    text = "\n".join(
        f"{request.artifact_id} | {request.repair_type.value} | "
        f"{request.status.value} | {request.user_message}"
        for request in requests
    )
    return DiagnosticsActionResult(
        action_id,
        "success",
        f"Prepared {len(requests)} artifact repair request(s).",
        output_text=text,
    )


def validate_artifact_registry(
    action_id: str,
    context: DiagnosticsActionContext,
) -> DiagnosticsActionResult:
    """Validate artifact registry shape for diagnostics."""

    requests = ArtifactRepairService().build_repair_requests(
        context.session,
        context.mode_registry,
    )
    generators = built_in_generator_registry().registrations()
    missing = diag_summary.missing_artifact_count(context.session, context.mode_registry)
    status = "warning" if missing or requests else "success"
    text = "\n".join(
        (
            f"artifacts={_visible_artifact_count(context)}",
            f"missing={missing}",
            f"repair_requests={len(requests)}",
            f"generators={len(generators)}",
            "headless_generators="
            + ", ".join(item.generator_id for item in generators if item.can_run_headless),
            "live_layout_required="
            + ", ".join(item.generator_id for item in generators if item.requires_live_layout),
        )
    )
    return DiagnosticsActionResult(action_id, status, "Artifact registry validated.", text)


def export_artifact_health_report(
    action_id: str,
    context: DiagnosticsActionContext,
) -> DiagnosticsActionResult:
    """Write a text artifact health report into the session folder."""

    if context.paths is None:
        return DiagnosticsActionResult(
            action_id,
            "unavailable",
            "Artifact health report export needs a session folder.",
        )
    _session, result = ArtifactRepairService().scan_session(
        context.session,
        context.paths,
        context.mode_registry,
    )
    destination = context.paths.folder / "artifact_health_report.txt"
    destination.write_text(artifact_health_text(result), encoding="utf-8")
    return DiagnosticsActionResult(
        "ExportArtifactHealthReport",
        "success",
        "Artifact health report exported.",
        output_path=str(destination),
    )


def artifact_health_text(result: ArtifactScanResult) -> str:
    """Return a text serialization of an artifact health scan."""

    return "\n".join(
        (
            f"session_id={result.session_id}",
            f"checked_at={result.checked_at}",
            f"artifact_count={result.artifact_count}",
            f"present={result.present_count}",
            f"missing={result.missing_count}",
            f"stale={result.stale_count}",
            f"failed={result.failed_count}",
            f"placeholder={result.placeholder_count}",
            "warning_ids=" + ", ".join(result.warning_ids),
            "repair_candidates=" + ", ".join(result.repair_candidates),
        )
    )


def _visible_artifact_count(context: DiagnosticsActionContext) -> int:
    return sum(
        1
        for artifact in (context.session.artifacts or {}).values()
        if artifact_visible_for_session(context.session, artifact, context.mode_registry)
    )
