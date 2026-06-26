"""Mode-aware warning visibility helpers."""

from __future__ import annotations

from metrology_process_planner.domains.modes.mode_registry import ModeRegistry
from metrology_process_planner.domains.session.record import SessionRecord
from metrology_process_planner.domains.warnings.warnings import WarningRecord

_PROCESS_WARNING_CODES = frozenset(
    {
        "SOLVER_BACKEND_UNAVAILABLE",
        "RENDER_PROFILE_MISSING",
        "PROCESS_OUTPUT_STALE",
        "PROCESS_OUTPUT_REGENERATION_FAILED",
    }
)

_PROCESS_WARNING_SOURCES = frozenset(
    {
        "process_context",
        "process_output",
        "process_solver",
        "solver",
        "render_profile",
    }
)


def session_is_process_aware(session: SessionRecord) -> bool:
    """Return whether the active session mode exposes process context."""

    from metrology_process_planner.domains.modes.mode_registry import built_in_mode_registry

    mode = built_in_mode_registry().definition(session.mode.value)
    return (
        mode.family == "process_aware"
        or mode.capabilities.supports_process_solver
        or mode.process.recipe_policy not in {"forbidden", "optional_hidden"}
    )


def warning_visible_for_session(
    session: SessionRecord,
    warning: WarningRecord,
    mode_registry: ModeRegistry | None = None,
) -> bool:
    """Return whether a warning belongs in normal mode-scoped UI/export surfaces."""

    return _session_is_process_aware(session, mode_registry) or not is_process_warning(warning)


def is_process_warning(warning: WarningRecord) -> bool:
    """Return whether a warning is process-context specific."""

    return (
        warning.source in _PROCESS_WARNING_SOURCES
        or warning.code.startswith("PROCESS_")
        or warning.code in _PROCESS_WARNING_CODES
    )


def _session_is_process_aware(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    if mode_registry is None:
        return session_is_process_aware(session)
    mode = mode_registry.definition(session.mode.value)
    return (
        mode.family == "process_aware"
        or mode.capabilities.supports_process_solver
        or mode.process.recipe_policy not in {"forbidden", "optional_hidden"}
    )
