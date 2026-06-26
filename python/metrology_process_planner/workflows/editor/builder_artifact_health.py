"""Artifact health and detail view-model builders."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ArtifactRecord, ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import (
    ArtifactDetailViewModel,
    ArtifactHealthViewModel,
)


def artifact_health(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> ArtifactHealthViewModel:
    """Return aggregate artifact health counts for a session."""

    counts: dict[str, int] = {}
    for artifact in (session.artifacts or {}).values():
        if not artifact_visible_for_session(session, artifact, mode_registry):
            continue
        counts[artifact.status.value] = counts.get(artifact.status.value, 0) + 1
    return ArtifactHealthViewModel(
        present=counts.get("present", 0),
        missing=counts.get("missing", 0),
        stale=counts.get("stale", 0),
        failed=counts.get("failed", 0),
        placeholder=counts.get("placeholder", 0),
        pending=counts.get("pending", 0),
        external=counts.get("external", 0),
        superseded=counts.get("superseded", 0),
        intentionally_ignored=counts.get("intentionally_ignored", 0),
    )


def artifact_details(
    items: Mapping[str, SessionItem],
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> dict[str, tuple[ArtifactDetailViewModel, ...]]:
    """Return per-editor-item artifact detail rows."""

    artifacts = session.artifacts or {}
    details: dict[str, tuple[ArtifactDetailViewModel, ...]] = {}
    for item_id, item in items.items():
        item_artifacts = tuple(
            artifacts[ref.artifact_id]
            for ref in item.artifact_refs
            if ref.artifact_id in artifacts
            and artifact_visible_for_session(session, artifacts[ref.artifact_id], mode_registry)
        )
        if item_artifacts:
            details[item_id] = tuple(_artifact_detail(artifact) for artifact in item_artifacts)
    return details


def _artifact_detail(artifact: ArtifactRecord) -> ArtifactDetailViewModel:
    return ArtifactDetailViewModel(
        artifact_id=artifact.id,
        label=artifact.label,
        artifact_type=artifact.type,
        status=artifact.status.value,
        path=artifact.relative_path,
        generator=artifact.generator,
        generated_at=artifact.generated_at,
        dependency_count=len(artifact.dependencies),
        repair_available=artifact.repair.regenerable,
        warning_ids=artifact.warning_ids,
    )
