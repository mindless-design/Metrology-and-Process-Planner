"""Summary row helpers for Advanced Diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from metrology_process_planner.app.diagnostics_artifact_summary import (
    artifact_generator_summary,
    artifact_repair_queue_summary,
    artifact_summary,
)
from metrology_process_planner.app.diagnostics_artifact_summary import (
    missing_artifact_count as _missing_artifact_count,
)
from metrology_process_planner.app.diagnostics_selection import editor_selection_rows
from metrology_process_planner.app.diagnostics_state import workflow_state_rows
from metrology_process_planner.app.diagnostics_windows import open_windows_summary
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.diagnostics import DiagnosticEvent
from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.domains.session.display_units import (
    display_unit_preferences_from_session,
    format_unit_summary,
)
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)
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
        ("Display Units", format_unit_summary(display_unit_preferences_from_session(session))),
        ("Loaded Mode Definition", _loaded_mode_definition(session, mode_registry)),
        *mode_policy_rows(session, mode_registry),
        *workflow_state_rows(session, mode_registry),
        *editor_selection_rows(editor_document),
        ("Loaded Modes", _loaded_modes(session, mode_registry)),
        ("Mode Validation", mode_validation_summary(session)),
        ("Artifacts", artifact_summary(session, mode_registry)),
        ("Artifact Repair Queue", artifact_repair_queue_summary(session, mode_registry)),
        ("Artifact Generators", artifact_generator_summary()),
        ("Warnings", str(_visible_warning_count(session, mode_registry))),
        ("Warning Codes", _warning_codes(session, mode_registry)),
        ("Missing Artifacts", str(missing_artifact_count(session, mode_registry))),
        ("Recent Commands", _recent_commands(recent_events)),
        ("Recent Failures", recent_failure_summary(recent_events)),
        ("Recent Events", _recent_event_names(recent_events)),
        ("Recent Event Count", str(len(recent_events))),
        ("Open Windows", open_windows_summary(window_registry)),
    )


def missing_artifact_count(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> int:
    """Return the visible missing artifact count for diagnostics callers."""

    return _missing_artifact_count(session, mode_registry)


def mode_policy_rows(
    session: SessionRecord,
    mode_registry: ModeRegistry,
) -> tuple[tuple[str, str], ...]:
    """Return active mode process-awareness diagnostics."""

    mode = mode_registry.definition(session.mode.value)
    recipe_required = mode.process.recipe_policy == "required"
    process_aware = _mode_is_process_aware(mode)
    process_visible = mode.editor.process_context_visible
    return (
        ("Mode Process Aware", str(process_aware).lower()),
        ("Recipe Required", str(recipe_required).lower()),
        ("Solver Operation", mode.process.solver_operation or "none"),
        ("Process Context Visible", str(process_visible).lower()),
    )


def _mode_is_process_aware(mode: ModeDefinition) -> bool:
    return (
        mode.family == "process_aware"
        or mode.capabilities.supports_process_solver
        or mode.process.recipe_policy not in {"forbidden", "optional_hidden"}
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


def _loaded_mode_definition(session: SessionRecord, mode_registry: ModeRegistry) -> str:
    mode = mode_registry.definition(session.mode.value)
    return (
        f"{mode.mode_id} ({mode.display_name}, family={mode.family}, "
        f"version={mode.version})"
    )


def _loaded_modes(session: SessionRecord, mode_registry: ModeRegistry) -> str:
    requested = dict(session.extensions or {}).get("mode_validation", {})
    requested_mode = requested.get("requested_mode") if isinstance(requested, dict) else None
    modes = list(mode_registry.mode_ids())
    if requested_mode and requested_mode not in modes:
        modes.append(str(requested_mode))
    return ", ".join(modes)


def _warning_codes(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> str:
    codes = sorted(
        {
            warning.code
            for warning in session.warnings
            if warning.code and warning_visible_for_session(session, warning, mode_registry)
        }
    )
    return ", ".join(codes) if codes else "none"


def _visible_warning_count(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> int:
    return sum(
        1
        for warning in session.warnings
        if warning_visible_for_session(session, warning, mode_registry)
    )


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
    return cast(str, label)
