"""Readiness-aware Reporting Workbench action presentation."""

from __future__ import annotations

from metrology_process_planner.reporting.readiness import ReadinessStatus, ReportReadiness
from metrology_process_planner.ui.reporting_workbench.view_models import ReportingWorkbenchAction
from metrology_process_planner.ui.shell import CommandRouteResult


def primary_action_id(readiness: ReportReadiness) -> str:
    """Return the primary action for the current readiness state."""

    if readiness.status is ReadinessStatus.STALE_OUTPUTS:
        return "regenerate_stale"
    if readiness.status is ReadinessStatus.VALIDATION_FAILED:
        return "regenerate_missing"
    if readiness.status is ReadinessStatus.MISSING_REQUIRED_ARTIFACTS:
        return "regenerate_missing"
    return "export_pptx"


def workbench_actions(
    readiness: ReportReadiness,
    last_result: CommandRouteResult | None = None,
) -> tuple[ReportingWorkbenchAction, ...]:
    """Return readiness-aware action buttons."""

    can_export = readiness.can_generate()
    primary = primary_action_id(readiness)
    actions: tuple[ReportingWorkbenchAction, ...] = (
        ReportingWorkbenchAction("validate", "Validate Report"),
        ReportingWorkbenchAction("regenerate_missing", "Regenerate Missing", True, "", primary),
        ReportingWorkbenchAction("regenerate_stale", "Regenerate Stale", True, "", primary),
        ReportingWorkbenchAction("export_pptx", _pptx_label(readiness), can_export, "", primary),
        ReportingWorkbenchAction("export_pdf", "Export PDF", can_export),
        ReportingWorkbenchAction("export_csv", "Export CSV", can_export),
        ReportingWorkbenchAction("export_images", "Export Image Bundle", can_export),
        ReportingWorkbenchAction("choose_output", "Choose Output Folder"),
        ReportingWorkbenchAction("open_output", "Open Output Folder"),
        ReportingWorkbenchAction("close", "Close"),
    )
    if last_result is not None and last_result.output_path:
        actions += (
            ReportingWorkbenchAction("open_report", "Open Report"),
            ReportingWorkbenchAction("regenerate_report", "Regenerate Report"),
        )
    return actions


def _pptx_label(readiness: ReportReadiness) -> str:
    if readiness.status is ReadinessStatus.READY_WITH_WARNINGS:
        return "Export with Placeholders"
    return "Export PowerPoint"
