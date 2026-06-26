"""Additional diagnostics rows required by the dashboard shell."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, ReportRecord, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.document import SessionDocument


def with_dashboard_context_rows(
    rows: tuple[tuple[str, str], ...],
    session: SessionRecord,
    paths: SessionPaths | None,
    document: SessionDocument | None,
    mode_registry: ModeRegistry | None = None,
) -> tuple[tuple[str, str], ...]:
    """Append dashboard-specific session, runtime, and report rows."""

    return rows + (
        ("Active Session ID", session.id),
        ("Session Path", _session_path(paths, document)),
        ("Active Session Path", _session_path(paths, document)),
        ("Dirty State", _dirty_state(document)),
        ("Active Mode", session.mode.value),
        ("Solver Backend", session.process_context.solver_backend or "none"),
        ("Renderer Backend", session.process_context.render_profile or "default"),
        ("Report Readiness", _report_readiness(session, mode_registry)),
    )


def with_open_window_rows(
    rows: tuple[tuple[str, str], ...],
    open_windows: str,
) -> tuple[tuple[str, str], ...]:
    """Replace the open-window summary row after the diagnostics shell opens."""

    return tuple(
        (key, open_windows) if key == "Open Windows" else (key, value)
        for key, value in rows
    )


def _session_path(paths: SessionPaths | None, document: SessionDocument | None) -> str:
    if document is not None and document.loaded_path is not None:
        return str(document.loaded_path)
    if paths is not None:
        return str(paths.session_json)
    return "unavailable"


def _dirty_state(document: SessionDocument | None) -> str:
    if document is None:
        return "unknown"
    return "dirty" if document.dirty_state.is_dirty else "clean"


def _report_readiness(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> str:
    if not session.reports:
        return "not requested"
    ready = sum(
        1
        for report in session.reports
        if _report_has_visible_artifact(session, report, mode_registry)
    )
    return f"{ready}/{len(session.reports)} reports have artifacts"


def _report_has_visible_artifact(
    session: SessionRecord,
    report: ReportRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    artifact_refs = report.artifact_refs or {}
    artifacts = session.artifacts or {}
    return any(
        (artifact := artifacts.get(artifact_id)) is not None
        and artifact_visible_for_session(session, artifact, mode_registry)
        for artifact_id in artifact_refs.values()
    )
