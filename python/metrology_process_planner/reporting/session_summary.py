"""Derived session-level summaries for reports."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware
from metrology_process_planner.workflows.editor.document import SessionDocument


def process_context_summary(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> dict[str, object]:
    """Return process context data only for process-aware sessions."""

    if not mode_is_process_aware(session, mode_registry):
        return {}
    return dict(session.process_context.to_dict())


def session_summary(
    document: SessionDocument,
    mode_registry: ModeRegistry | None = None,
) -> dict[str, object]:
    """Return report-ready session summary counts."""

    session = document.session
    return {
        "session_id": session.id,
        "session_name": session.name,
        "mode": session.mode.value,
        "captures": len(session.captures),
        "measurements": sum(len(capture.measurements) for capture in session.captures),
        "grid_datasets": len(session.grid_datasets),
        "artifacts": sum(
            1
            for artifact in (session.artifacts or {}).values()
            if artifact_visible_for_session(session, artifact, mode_registry)
        ),
        "warnings": sum(
            1
            for warning in session.warnings
            if warning_visible_for_session(session, warning, mode_registry)
        ),
    }
