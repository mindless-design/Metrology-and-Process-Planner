"""Status and inspector helpers for the Reporting Workbench."""

from __future__ import annotations

from metrology_process_planner.reporting.readiness import ReadinessStatus, ReportReadiness
from metrology_process_planner.ui.shell import CommandRouteResult


def readiness_label(status: ReadinessStatus) -> str:
    """Return a compact user-facing readiness label."""

    labels = {
        ReadinessStatus.READY: "Ready",
        ReadinessStatus.READY_WITH_WARNINGS: "Ready with warnings",
        ReadinessStatus.MISSING_REQUIRED_ARTIFACTS: "Missing required artifacts",
        ReadinessStatus.STALE_OUTPUTS: "Stale outputs",
        ReadinessStatus.INVALID_SESSION: "Invalid session",
        ReadinessStatus.EXPORT_BLOCKED: "Export blocked",
        ReadinessStatus.VALIDATION_FAILED: "Validation failed",
    }
    return labels[status]


def readiness_groups(readiness: ReportReadiness) -> tuple[tuple[str, str], ...]:
    """Return grouped readiness details for the inspector."""

    return (
        ("Blocking", str(len(readiness.blocking_issues))),
        ("Placeholdered", ", ".join(readiness.missing_required_artifacts)),
        ("Stale", ", ".join(readiness.stale_artifacts)),
        ("Optional", ", ".join(readiness.missing_optional_artifacts)),
        ("Warnings", str(len(readiness.warnings))),
        ("Repairs", "; ".join(readiness.suggested_repairs)),
    )


def route_result_fields(result: CommandRouteResult | None) -> tuple[tuple[str, str], ...]:
    """Return export/result fields for the workbench model."""

    if result is None:
        return ()
    fields: tuple[tuple[str, str], ...] = (("Last Action", result.status),)
    if result.message:
        fields += (("Message", result.message),)
    if result.output_path:
        fields += (("Output", result.output_path),)
    return fields
