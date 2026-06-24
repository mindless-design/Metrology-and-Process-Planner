"""Action view models for the Advanced Diagnostics surface."""

from __future__ import annotations

from metrology_process_planner.infrastructure.diagnostics import DiagnosticEvent
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.ui.shell.view_models import EditorActionViewModel


def diagnostics_actions(
    paths: SessionPaths | None,
    recent_events: tuple[DiagnosticEvent, ...],
) -> tuple[EditorActionViewModel, ...]:
    """Return modeless diagnostics actions with disabled reasons."""

    has_paths = paths is not None
    has_events = bool(recent_events)
    return (
        EditorActionViewModel("ExportDiagnosticsBundle", "Export Diagnostics Bundle"),
        _action(
            "CopyCommandTrace",
            "Copy Command Trace",
            has_events,
            "No command or diagnostic events are available yet.",
        ),
        _action(
            "OpenSessionFolder",
            "Open Session Folder",
            has_paths,
            "No session folder is associated with diagnostics.",
        ),
        _action(
            "ScanArtifacts",
            "Scan Artifacts",
            has_paths,
            "No session folder is available for artifact scanning.",
        ),
        EditorActionViewModel("ValidateSession", "Validate Session"),
        EditorActionViewModel("ValidateModes", "Validate Modes"),
    )


def _action(
    action_id: str,
    label: str,
    enabled: bool,
    disabled_reason: str,
) -> EditorActionViewModel:
    reason = "" if enabled else disabled_reason
    return EditorActionViewModel(action_id, label, enabled=enabled, disabled_reason=reason)


__all__ = ["diagnostics_actions"]
