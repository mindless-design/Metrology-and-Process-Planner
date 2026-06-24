"""Diagnostics contracts, sinks, seam checks, and bundle helpers."""

from metrology_process_planner.infrastructure.diagnostics_assertions import (
    assert_editor_canvas_selection_synced,
    assert_no_diagnostic_errors,
    assert_no_missing_artifacts,
    assert_pending_promoted_to_saved,
    assert_seam_ok,
    assert_trace_contains,
    assert_warning_created,
)
from metrology_process_planner.infrastructure.diagnostics_bundle import DiagnosticsService
from metrology_process_planner.infrastructure.diagnostics_diffs import (
    diff_manifest_vs_filesystem,
    diff_parent_child_integrity,
    diff_pending_state,
    diff_session_vs_canvas,
    diff_session_vs_editor,
    diff_session_vs_filesystem,
)
from metrology_process_planner.infrastructure.diagnostics_models import (
    DiagnosticEvent,
    DiagnosticsSnapshot,
    DiffResult,
)
from metrology_process_planner.infrastructure.diagnostics_seams import (
    check_editor_canvas_selection_seam,
    check_pending_to_saved_seam,
    check_session_to_editor_seam,
    check_session_to_filesystem_seam,
)
from metrology_process_planner.infrastructure.diagnostics_sinks import (
    CompositeDiagnosticSink,
    DiagnosticSink,
    InMemoryDiagnosticSink,
    JsonlDiagnosticSink,
    ListDiagnosticSink,
)
from metrology_process_planner.infrastructure.diagnostics_snapshots import (
    build_diagnostics_snapshot,
    snapshot_artifact_manifest,
    snapshot_canvas_objects,
    snapshot_editor_view_model,
    snapshot_filesystem_artifacts,
    snapshot_overlay_manager,
    snapshot_report_model,
    snapshot_session_document,
    snapshot_workflow_state,
)
from metrology_process_planner.infrastructure.diagnostics_timeline import summarize_trace_timeline
from metrology_process_planner.infrastructure.trace_context import TraceContext

__all__ = [
    "CompositeDiagnosticSink",
    "DiagnosticEvent",
    "DiagnosticSink",
    "DiagnosticsService",
    "DiagnosticsSnapshot",
    "DiffResult",
    "InMemoryDiagnosticSink",
    "JsonlDiagnosticSink",
    "ListDiagnosticSink",
    "TraceContext",
    "assert_editor_canvas_selection_synced",
    "assert_no_diagnostic_errors",
    "assert_no_missing_artifacts",
    "assert_pending_promoted_to_saved",
    "assert_seam_ok",
    "assert_trace_contains",
    "assert_warning_created",
    "build_diagnostics_snapshot",
    "check_editor_canvas_selection_seam",
    "check_pending_to_saved_seam",
    "check_session_to_editor_seam",
    "check_session_to_filesystem_seam",
    "diff_manifest_vs_filesystem",
    "diff_parent_child_integrity",
    "diff_pending_state",
    "diff_session_vs_canvas",
    "diff_session_vs_editor",
    "diff_session_vs_filesystem",
    "snapshot_artifact_manifest",
    "snapshot_canvas_objects",
    "snapshot_editor_view_model",
    "snapshot_filesystem_artifacts",
    "snapshot_overlay_manager",
    "snapshot_report_model",
    "snapshot_session_document",
    "snapshot_workflow_state",
    "summarize_trace_timeline",
]
