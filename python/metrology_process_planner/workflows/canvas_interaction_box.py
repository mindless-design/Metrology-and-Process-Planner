"""Box release helpers for canvas interaction."""

from __future__ import annotations

from typing import Optional

from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.trace_context import TraceContext
from metrology_process_planner.domains.geometry import Point
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.workflows.canvas_interaction_commit import (
    commit_pending_box,
    invalid_release_result,
)
from metrology_process_planner.workflows.canvas_interaction_drag import update_box_drag
from metrology_process_planner.workflows.canvas_interaction_models import (
    InteractionContext,
    InteractionResult,
)
from metrology_process_planner.workflows.canvas_state import find_canvas_object


def release_box(
    sink: Optional[DiagnosticSink],
    session: SessionRecord,
    context: InteractionContext,
    end: Point,
    shift_pressed: bool,
    trace_context: Optional[TraceContext],
    mode_registry: ModeRegistry | None = None,
) -> InteractionResult:
    """Commit a valid box preview into a pending capture."""

    updated = update_box_drag(sink, session, context, end, shift_pressed, trace_context)
    if not updated.handled:
        return updated
    preview = find_canvas_object(updated.session, str(context.live_preview_id))
    if preview is None or preview.geometry.bounds is None:
        return InteractionResult(session=updated.session, context=context, handled=False)
    warnings = preview.geometry.validate()
    if warnings:
        return invalid_release_result(sink, trace_context, updated, preview, warnings)
    return commit_pending_box(sink, trace_context, updated, preview, mode_registry)
