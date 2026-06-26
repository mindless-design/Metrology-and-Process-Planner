"""First-class diagnostics package."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS = {
    "CompositeDiagnosticSink": "metrology_process_planner.diagnostics.diagnostics_sinks",
    "DiagnosticEvent": "metrology_process_planner.diagnostics.diagnostics_models",
    "DiagnosticSink": "metrology_process_planner.diagnostics.diagnostics_sinks",
    "DiagnosticsService": "metrology_process_planner.diagnostics.diagnostics_bundle",
    "DiagnosticsSnapshot": "metrology_process_planner.diagnostics.diagnostics_models",
    "DiffResult": "metrology_process_planner.diagnostics.diagnostics_models",
    "InMemoryDiagnosticSink": "metrology_process_planner.diagnostics.diagnostics_sinks",
    "JsonlDiagnosticSink": "metrology_process_planner.diagnostics.diagnostics_sinks",
    "ListDiagnosticSink": "metrology_process_planner.diagnostics.diagnostics_sinks",
    "TraceContext": "metrology_process_planner.diagnostics.trace_context",
    "assert_editor_canvas_selection_synced": (
        "metrology_process_planner.diagnostics.diagnostics_assertions"
    ),
    "assert_no_diagnostic_errors": "metrology_process_planner.diagnostics.diagnostics_assertions",
    "assert_no_missing_artifacts": "metrology_process_planner.diagnostics.diagnostics_assertions",
    "assert_pending_promoted_to_saved": (
        "metrology_process_planner.diagnostics.diagnostics_assertions"
    ),
    "assert_seam_ok": "metrology_process_planner.diagnostics.diagnostics_assertions",
    "assert_trace_contains": "metrology_process_planner.diagnostics.diagnostics_assertions",
    "assert_warning_created": "metrology_process_planner.diagnostics.diagnostics_assertions",
    "build_diagnostics_snapshot": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "check_editor_canvas_selection_seam": (
        "metrology_process_planner.diagnostics.diagnostics_seams"
    ),
    "check_pending_to_saved_seam": "metrology_process_planner.diagnostics.diagnostics_seams",
    "check_session_to_editor_seam": "metrology_process_planner.diagnostics.diagnostics_seams",
    "check_session_to_filesystem_seam": "metrology_process_planner.diagnostics.diagnostics_seams",
    "diff_manifest_vs_filesystem": "metrology_process_planner.diagnostics.diagnostics_diffs",
    "diff_parent_child_integrity": "metrology_process_planner.diagnostics.diagnostics_diffs",
    "diff_pending_state": "metrology_process_planner.diagnostics.diagnostics_diffs",
    "diff_session_vs_canvas": "metrology_process_planner.diagnostics.diagnostics_diffs",
    "diff_session_vs_editor": "metrology_process_planner.diagnostics.diagnostics_diffs",
    "diff_session_vs_filesystem": "metrology_process_planner.diagnostics.diagnostics_diffs",
    "snapshot_artifact_manifest": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "snapshot_canvas_objects": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "snapshot_editor_view_model": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "snapshot_filesystem_artifacts": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "snapshot_overlay_manager": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "snapshot_report_model": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "snapshot_session_document": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "snapshot_workflow_state": "metrology_process_planner.diagnostics.diagnostics_snapshots",
    "summarize_trace_timeline": "metrology_process_planner.diagnostics.diagnostics_timeline",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load public diagnostics exports on first access."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
