"""Canonical session JSON serialization and migration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

from metrology_process_planner.domains.session.canonical import SessionIdentity
from metrology_process_planner.domains.session.record import session_mode_value
from metrology_process_planner.domains.session.serialization_load import session_from_dict
from metrology_process_planner.domains.session.workflow import WorkflowState

__all__ = ("session_from_dict", "session_to_dict")


def session_to_dict(session: Any) -> dict[str, Any]:
    """Serialize a session in canonical v5 shape."""

    artifacts = session.artifacts or {}
    return {
        "schema": session.schema.to_dict(),
        "session": _identity(session).to_dict(),
        "paths": session.paths.to_dict(),
        "source_layout": session.source_layout.to_dict(),
        "coordinates": session.coordinates.to_dict(),
        "setup": session.setup.to_dict(),
        "captures": [capture.to_dict() for capture in session.captures],
        "grid_datasets": [dataset.to_dict() for dataset in session.grid_datasets],
        "process_context": session.process_context.to_dict(),
        "process_outputs": [output.to_dict() for output in session.process_outputs],
        "reports": [report.to_dict() for report in session.reports],
        "artifacts": {
            artifact_id: artifact.to_dict()
            for artifact_id, artifact in sorted(artifacts.items())
        },
        "warnings": [warning.to_dict() for warning in session.warnings],
        "workflow": _workflow_with_pending(session).to_dict(),
        "extensions": _extensions_with_runtime_state(session),
        "audit": [event.to_dict() for event in session.audit],
    }


def _identity(session: Any) -> SessionIdentity:
    return SessionIdentity(
        session.id,
        session.name,
        session_mode_value(session.mode),
        session.created_at,
        session.updated_at,
    )


def _workflow_with_pending(session: Any) -> WorkflowState:
    workflow = cast(WorkflowState, session.workflow)
    if workflow.pending_item_ref or not session.pending_captures:
        return workflow
    return replace(workflow, pending_item_ref=session.pending_captures[0].id)


def _extensions_with_runtime_state(session: Any) -> dict[str, Any]:
    extensions = dict(session.extensions or {})
    canvas_extension = dict(extensions.get("canvas", {}))
    if session.canvas_objects:
        canvas_extension["canvas_objects"] = [item.to_dict() for item in session.canvas_objects]
    if session.pending_captures:
        canvas_extension["pending_captures"] = [item.to_dict() for item in session.pending_captures]
    if canvas_extension:
        extensions["canvas"] = canvas_extension
    return extensions
