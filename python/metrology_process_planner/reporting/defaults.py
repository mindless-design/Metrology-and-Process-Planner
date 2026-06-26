"""Default report request choices shared by app and workflow callers."""

from __future__ import annotations

from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.reporting.requests import ReportRequest
from metrology_process_planner.workflows.editor.document import SessionDocument


def default_report_request(document: SessionDocument, paths: SessionPaths) -> ReportRequest:
    """Return the mode-aware default report request."""

    template_id = default_template_id(document.session.mode.value)
    return ReportRequest(document.session.id, template_id, output_dir=paths.reports_dir)


def default_template_id(mode_id: str) -> str:
    """Return the default template id for a session mode."""

    if "cad" in mode_id:
        return "cad_review_report"
    if "fib" in mode_id:
        return "fib_planning_package"
    if "process_flow" in mode_id or mode_id == "process_flow_summary":
        return "process_flow_summary"
    if any(token in mode_id for token in ("optical", "cdsem", "metrology")):
        return "metrology_report"
    if any(token in mode_id for token in ("process", "profilometry", "ellipsometry")):
        return "process_review"
    return "capture_catalog"
