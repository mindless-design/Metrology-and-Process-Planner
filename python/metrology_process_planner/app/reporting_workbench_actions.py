"""Action helpers for the modeless Reporting Workbench controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.reporting_workbench_exports import export_report_action
from metrology_process_planner.ui.shell import CommandRouteResult

if TYPE_CHECKING:
    from metrology_process_planner.app.reporting_workbench import ReportingWorkbenchController


def dispatch_workbench_action(
    controller: ReportingWorkbenchController,
    action_id: str,
) -> CommandRouteResult:
    """Dispatch a modeless workbench action."""

    if action_id.startswith("export_"):
        return export_report_action(controller, action_id)
    if action_id == "validate":
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "success",
            "Report validation refreshed.",
        )
    if action_id in {"regenerate_missing", "regenerate_stale"}:
        return regenerate_artifacts_action(controller, action_id)
    if action_id == "open_output":
        return open_output_action(controller)
    if action_id == "choose_output":
        return controller.choose_output_dir()
    if action_id == "open_report":
        return open_report_action(controller)
    if action_id == "regenerate_report":
        return export_report_action(controller, "export_pptx")
    if action_id == "close":
        return close_action(controller)
    return CommandRouteResult(
        CommandId.OPEN_REPORTING_WORKBENCH,
        "unavailable",
        f"Unknown report action: {action_id}",
    )


def open_output_action(controller: ReportingWorkbenchController) -> CommandRouteResult:
    """Resolve the report output folder for a workbench action."""

    if controller.current_paths is None:
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "unavailable",
            "No report output folder is available.",
        )
    return CommandRouteResult(
        CommandId.OPEN_REPORTING_WORKBENCH,
        "success",
        "Open report output folder.",
        output_path=str(controller.current_paths.reports_dir),
    )


def open_report_action(controller: ReportingWorkbenchController) -> CommandRouteResult:
    """Return the last generated report path for shell handoff."""

    result = controller.last_result
    if result is None or not result.output_path:
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "unavailable",
            "No generated report is available.",
        )
    return CommandRouteResult(
        CommandId.OPEN_REPORTING_WORKBENCH,
        "success",
        "Open generated report.",
        output_path=result.output_path,
    )


def regenerate_artifacts_action(
    controller: ReportingWorkbenchController,
    action_id: str,
) -> CommandRouteResult:
    """Regenerate report artifacts through the injected repair service."""

    repair_service = controller.artifact_repair_service
    if repair_service is None:
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "unavailable",
            "ArtifactRepairService is not attached.",
        )
    if controller.current_document is None or controller.current_paths is None:
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "unavailable",
            "No active report document.",
        )
    repair_method = (
        repair_service.regenerate_stale
        if action_id == "regenerate_stale"
        else repair_service.regenerate_missing
    )
    repaired = repair_method(controller.current_document, controller.current_paths)
    controller.replace_after_export(repaired.session)
    return CommandRouteResult(
        CommandId.OPEN_REPORTING_WORKBENCH,
        "success",
        _regenerate_message(action_id),
    )


def _regenerate_message(action_id: str) -> str:
    if action_id == "regenerate_stale":
        return "Stale report artifacts regenerated."
    return "Missing report artifacts regenerated."


def close_action(controller: ReportingWorkbenchController) -> CommandRouteResult:
    """Close the workbench window for the active session."""

    if controller.current_document is not None:
        controller.window_registry.close(
            f"reporting_workbench:{controller.current_document.session.id}"
        )
    return CommandRouteResult(
        CommandId.OPEN_REPORTING_WORKBENCH,
        "success",
        "Reporting Workbench closed.",
    )
