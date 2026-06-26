"""Setup artifact references for unified editor document building."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ArtifactRecord, ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.builder_artifact_refs import (
    _artifact_ref_from_record,
    _warning_lookups,
)
from metrology_process_planner.workflows.editor.references import ArtifactRef


def setup_artifact_refs(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[ArtifactRef, ...]:
    """Return visible setup-owned artifacts for the unified setup item."""

    warnings = _warning_lookups(session, mode_registry)
    return tuple(
        _artifact_ref_from_record(artifact, *warnings)
        for artifact in _visible_setup_artifacts(session, mode_registry)
    )


def _visible_setup_artifacts(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[ArtifactRecord, ...]:
    artifacts = session.artifacts or {}
    return tuple(
        artifact
        for artifact_id in _setup_artifact_ids(session)
        if (artifact := artifacts.get(artifact_id)) is not None
        and artifact_visible_for_session(session, artifact, mode_registry)
    )


def _setup_artifact_ids(session: SessionRecord) -> tuple[str, ...]:
    seen: set[str] = set()
    ids: list[str] = []
    for item in session.setup.items:
        for artifact_id in (item.artifact_refs or {}).values():
            if artifact_id not in seen:
                seen.add(artifact_id)
                ids.append(artifact_id)
    return tuple(ids)
