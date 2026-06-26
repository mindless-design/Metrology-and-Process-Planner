"""Editor-visible warning filters."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord, WarningRecord
from metrology_process_planner.domains.warnings.warning_visibility import (
    is_process_warning,
)
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware


def editor_visible_warnings(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[WarningRecord, ...]:
    """Return warnings that should appear in the unified editor."""

    if mode_is_process_aware(session, mode_registry):
        return session.warnings
    return tuple(
        warning
        for warning in session.warnings
        if not is_process_warning(warning)
        and _has_visible_warning_artifact(session, warning, mode_registry)
    )


def editor_visible_warning_count(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> int:
    """Return the count of warnings visible in the unified editor."""

    return len(editor_visible_warnings(session, mode_registry))


def _has_visible_warning_artifact(
    session: SessionRecord,
    warning: WarningRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    if not warning.related_artifact_refs:
        return True
    artifacts = session.artifacts or {}
    related = tuple(
        artifacts[artifact_id]
        for artifact_id in warning.related_artifact_refs
        if artifact_id in artifacts
    )
    if not related:
        return True
    return any(
        artifact_visible_for_session(session, artifact, mode_registry)
        for artifact in related
    )
