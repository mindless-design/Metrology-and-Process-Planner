"""Basic editor item builders and mode predicates."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.workflows.editor.builder_setup_artifacts import (
    setup_artifact_refs,
)
from metrology_process_planner.workflows.editor.document import SessionItem, SessionItemKind


def dashboard_item(session: SessionRecord) -> SessionItem:
    """Return the root dashboard item for a session."""

    return SessionItem(
        item_id="dashboard",
        kind=SessionItemKind.DASHBOARD,
        label=session.name,
        role="dashboard",
    )


def setup_item(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> SessionItem:
    """Return the setup navigator item."""

    return SessionItem(
        item_id="setup",
        kind=SessionItemKind.SETUP,
        label="Setup",
        role="setup",
        artifact_refs=setup_artifact_refs(session, mode_registry),
    )


def mode_uses_setup(session: SessionRecord, mode_registry: ModeRegistry | None = None) -> bool:
    """Return whether the current mode uses the setup guide."""

    registry = mode_registry or built_in_mode_registry()
    return registry.definition(session.mode.value).capabilities.uses_setup_guide


def mode_is_process_aware(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> bool:
    """Return whether the session mode has process-aware behavior."""

    mode = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    return (
        mode.family == "process_aware"
        or mode.capabilities.supports_process_solver
        or mode.process.recipe_policy not in {"forbidden", "optional_hidden"}
    )
