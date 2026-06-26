"""Output directory selection for the Reporting Workbench."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_path_adapter import PathSelection
from metrology_process_planner.reporting import ReportRequest
from metrology_process_planner.ui.shell import CommandRouteResult

if TYPE_CHECKING:
    from metrology_process_planner.app.reporting_workbench import ReportingWorkbenchController


def choose_report_output_dir(controller: ReportingWorkbenchController) -> CommandRouteResult:
    """Select and persist a report output folder on the current request."""

    if controller.current_document is None or controller.current_paths is None:
        return _output_result("unavailable", "No active report document.")
    current = controller.current_request or controller.default_request()
    selected = _select_output_dir(controller, current)
    if selected.status != "selected" or selected.path is None:
        return _output_result(selected.status, selected.message)
    controller.current_request = replace(current, output_dir=selected.path)
    return CommandRouteResult(
        CommandId.OPEN_REPORTING_WORKBENCH,
        "success",
        "Report output folder selected.",
        output_path=str(selected.path),
    )


def _select_output_dir(
    controller: ReportingWorkbenchController,
    request: ReportRequest,
) -> PathSelection:
    assert controller.current_paths is not None
    return controller.output_adapter.select_report_output_dir(
        request.resolved_output_dir(controller.current_paths.reports_dir),
    )


def _output_result(status: str, message: str) -> CommandRouteResult:
    return CommandRouteResult(CommandId.OPEN_REPORTING_WORKBENCH, status, message)
