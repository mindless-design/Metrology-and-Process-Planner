"""Test helper assertions backed by diagnostic events and seam checks."""

from __future__ import annotations

from metrology_process_planner.infrastructure.diagnostics_models import DiffResult
from metrology_process_planner.infrastructure.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.workflows.editor.document import SessionDocument


def assert_no_diagnostic_errors(sink: DiagnosticSink) -> None:
    """Raise AssertionError if the sink contains error or critical events."""

    errors = [event for event in sink.recent(10_000) if event.severity in {"error", "critical"}]
    if errors:
        details = "\n".join(f"{event.event_name}: {event.message}" for event in errors)
        raise AssertionError(f"Diagnostic errors were emitted:\n{details}")


def assert_trace_contains(
    sink: DiagnosticSink,
    trace_id: str,
    event_name: str,
) -> None:
    """Raise AssertionError if a trace does not contain an event."""

    events = sink.events_for_trace(trace_id)
    if not any(event.event_name == event_name for event in events):
        names = ", ".join(event.event_name for event in events)
        raise AssertionError(f"Trace {trace_id} did not contain {event_name}; saw [{names}].")


def assert_no_missing_artifacts(document: SessionDocument) -> None:
    """Raise AssertionError if an editor document has missing artifact refs."""

    missing = [
        f"{item.item_id}:{artifact.path}"
        for item in document.items_by_id.values()
        for artifact in item.artifact_refs
        if artifact.status == "missing"
    ]
    if missing:
        raise AssertionError("Missing artifacts in editor document: " + ", ".join(missing))


def assert_seam_ok(seam_name: str, result: DiffResult) -> None:
    """Raise AssertionError with seam details if a diff result failed."""

    if not result.ok:
        raise AssertionError(f"{seam_name} seam failed: {result.to_dict()}")


def assert_editor_canvas_selection_synced(document: SessionDocument) -> None:
    """Raise AssertionError if editor and canvas selected ids differ."""

    item = document.items_by_id.get(document.selection.selected_item_id)
    expected = set(item.canvas_object_ids if item is not None else ())
    actual = set(document.selection.selected_canvas_object_ids)
    if expected != actual:
        raise AssertionError(f"Editor/canvas selection mismatch: {expected} != {actual}")


def assert_pending_promoted_to_saved(sink: DiagnosticSink, trace_id: str) -> None:
    """Raise AssertionError if a trace lacks pending-to-saved events."""

    assert_trace_contains(sink, trace_id, "PendingCaptureCreated")
    assert_trace_contains(sink, trace_id, "CaptureRecordCreated")


def assert_warning_created(sink: DiagnosticSink, code: str) -> None:
    """Raise AssertionError if no warning event or warning id contains a code."""

    events = sink.recent(10_000)
    if not any(code in event.user_visible_warning_id or code in event.message for event in events):
        raise AssertionError(f"No warning diagnostic contained {code}.")
