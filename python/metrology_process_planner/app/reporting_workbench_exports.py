"""Reporting Workbench export command helpers."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.ui.shell import CommandRouteResult

if TYPE_CHECKING:
    from metrology_process_planner.app.reporting_workbench import ReportingWorkbenchController


def export_report_action(
    controller: ReportingWorkbenchController,
    action_id: str,
) -> CommandRouteResult:
    """Run a report export action for the active workbench document."""

    if (
        controller.current_document is None
        or controller.current_paths is None
        or controller.current_request is None
    ):
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "unavailable",
            "No active report document.",
        )
    format_name = _format_for_action(action_id)
    request = replace(controller.current_request, output_formats=(format_name,))
    result = controller._generation_service.generate(
        controller.current_document,
        request,
        controller.current_paths.folder,
    )
    if result.updated_session is not None:
        controller.replace_after_export(result.updated_session)
    if result.exported is None:
        return CommandRouteResult(
            CommandId.OPEN_REPORTING_WORKBENCH,
            "blocked",
            result.message or "Report export blocked.",
        )
    output_path = next(iter(result.exported.outputs.values()), result.exported.manifest_path)
    return CommandRouteResult(
        CommandId.OPEN_REPORTING_WORKBENCH,
        "success",
        result.message,
        output_path=str(output_path),
    )


def _format_for_action(action_id: str) -> str:
    return {
        "export_pptx": "pptx",
        "export_pdf": "pdf",
        "export_csv": "csv",
        "export_images": "images.zip",
    }.get(action_id, "pptx")
