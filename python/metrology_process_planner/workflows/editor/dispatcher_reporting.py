"""Report-oriented editor action handlers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from metrology_process_planner.reporting.backends import ExportedReport
from metrology_process_planner.reporting.defaults import default_report_request
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher


def build_report_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Generate a default report artifact from the current editor document."""

    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    from metrology_process_planner.reporting.service import ReportGenerationService

    request = default_report_request(document, dispatcher._paths)
    result = ReportGenerationService(mode_registry=dispatcher._mode_registry).generate(
        document,
        request,
        dispatcher._paths.folder,
    )
    if result.updated_session is None:
        return EditorActionResult(
            "blocked",
            document,
            result.message or "Report export is blocked.",
        )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(result.updated_session, document),
        result.message or "Report exported.",
        _report_output_path(result.exported),
    )


def _report_output_path(exported: ExportedReport | None) -> Path | None:
    if exported is None:
        return None
    if exported.outputs:
        return next(iter(exported.outputs.values()))
    return exported.manifest_path
