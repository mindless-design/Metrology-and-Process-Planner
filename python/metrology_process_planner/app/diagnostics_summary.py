"""Summary row helpers for Advanced Diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from metrology_process_planner.app.diagnostics_state import workflow_state_rows
from metrology_process_planner.app.diagnostics_windows import open_windows_summary
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.infrastructure.diagnostics import DiagnosticEvent
from metrology_process_planner.workflows.editor.document import SessionDocument


def diagnostics_summary_rows(
    session: SessionRecord,
    recent_events: tuple[DiagnosticEvent, ...],
    mode_registry: ModeRegistry,
    window_registry: WindowRegistry[object] | None = None,
    editor_document: SessionDocument | None = None,
) -> tuple[tuple[str, str], ...]:
    """Build the full Advanced Diagnostics summary table."""

    return (
        ("Status", "opened"),
        ("Message", "Advanced diagnostics resolved."),
        ("Session", f"{session.name} ({session.id})"),
        ("Mode", session.mode.value),
        *workflow_state_rows(session),
        *editor_selection_rows(editor_document),
        ("Loaded Modes", _loaded_modes(session, mode_registry)),
        ("Mode Validation", mode_validation_summary(session)),
        ("Artifacts", _artifact_summary(session)),
        ("Warnings", str(len(session.warnings))),
        ("Warning Codes", _warning_codes(session)),
        ("Missing Artifacts", str(missing_artifact_count(session))),
        ("Recent Commands", _recent_commands(recent_events)),
        ("Recent Failures", recent_failure_summary(recent_events)),
        ("Recent Events", _recent_event_names(recent_events)),
        ("Recent Event Count", str(len(recent_events))),
        ("Open Windows", open_windows_summary(window_registry)),
    )


def editor_selection_rows(
    document: SessionDocument | None,
) -> tuple[tuple[str, str], ...]:
    """Return selected editor and canvas state for diagnostics."""

    return (
        ("Selected Editor Item", _selected_editor_item(document)),
        ("Selected Canvas Object", _selected_canvas_objects(document)),
    )


def missing_artifact_count(session: SessionRecord) -> int:
    """Return the count of canonical artifacts marked missing."""

    return sum(
        1
        for artifact in (session.artifacts or {}).values()
        if artifact.status is ArtifactStatus.MISSING
    )


def mode_validation_summary(session: SessionRecord) -> str:
    """Return the mode validation status stored on the session."""

    validation = _mode_validation_extension(session)
    if not validation:
        return "ok"
    status = str(validation.get("status") or "warning")
    requested = str(validation.get("requested_mode") or "unknown")
    fallback = str(validation.get("fallback_mode") or "")
    if fallback:
        return f"{status}: {requested} -> {fallback}"
    return f"{status}: {requested}"


def recent_failure_summary(events: tuple[DiagnosticEvent, ...]) -> str:
    """Return a compact list of recent error or exception events."""

    failures = tuple(_failure_label(event) for event in events if _is_failure(event))
    failures = tuple(label for label in failures if label)
    return " | ".join(failures[-5:]) if failures else "none"


def _selected_editor_item(document: SessionDocument | None) -> str:
    if document is None:
        return "none"
    selected_id = document.selection.selected_item_id
    item = document.items_by_id.get(selected_id)
    if item is None:
        return selected_id or "none"
    return f"{item.label} ({item.item_id}, {item.status})"


def _selected_canvas_objects(document: SessionDocument | None) -> str:
    if document is None:
        return "none"
    canvas_ids = document.selection.selected_canvas_object_ids
    return ", ".join(canvas_ids) if canvas_ids else "none"


def _loaded_modes(session: SessionRecord, mode_registry: ModeRegistry) -> str:
    requested = dict(session.extensions or {}).get("mode_validation", {})
    requested_mode = requested.get("requested_mode") if isinstance(requested, dict) else None
    modes = list(mode_registry.mode_ids())
    if requested_mode and requested_mode not in modes:
        modes.append(str(requested_mode))
    return ", ".join(modes)


def _artifact_summary(session: SessionRecord) -> str:
    artifacts = tuple((session.artifacts or {}).values())
    if not artifacts:
        return "0 total"
    counts: dict[str, int] = {}
    for artifact in artifacts:
        counts[artifact.status.value] = counts.get(artifact.status.value, 0) + 1
    status_text = "; ".join(f"{key}={counts[key]}" for key in sorted(counts))
    return f"{len(artifacts)} total; {status_text}"


def _warning_codes(session: SessionRecord) -> str:
    codes = sorted({warning.code for warning in session.warnings if warning.code})
    return ", ".join(codes) if codes else "none"


def _recent_commands(events: tuple[DiagnosticEvent, ...]) -> str:
    commands = [event.operation for event in events if event.category == "command"]
    return ", ".join(commands[-5:]) if commands else "none"


def _recent_event_names(events: tuple[DiagnosticEvent, ...]) -> str:
    return ", ".join(event.event_name for event in events[-5:]) if events else "none"


def _mode_validation_extension(session: SessionRecord) -> Mapping[str, Any]:
    validation = dict(session.extensions or {}).get("mode_validation", {})
    return validation if isinstance(validation, Mapping) else {}


def _is_failure(event: DiagnosticEvent) -> bool:
    severity = event.severity.lower()
    return severity in {"error", "critical", "fatal"} or bool(event.exception_type)


def _failure_label(event: DiagnosticEvent) -> str:
    label = event.operation or event.event_name
    detail = event.exception_message or event.message
    if detail:
        return f"{label}: {detail}"
    return label
