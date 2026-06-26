"""Derived grid dataset summaries for reports."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    GridDatasetRecord,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)


def grid_dataset_summaries(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[dict[str, object], ...]:
    """Return report-ready summaries for session grid datasets."""

    return tuple(
        _grid_dataset_summary(session, dataset, mode_registry)
        for dataset in session.grid_datasets
    )


def _grid_dataset_summary(
    session: SessionRecord,
    dataset: GridDatasetRecord,
    mode_registry: ModeRegistry | None,
) -> dict[str, object]:
    metadata = dict(dataset.metadata or {})
    overview_id = dict(dataset.artifact_refs or {}).get("grid_overview", "")
    overview = _visible_overview_artifact(session, str(overview_id), mode_registry)
    return {
        "dataset_id": dataset.id,
        "label": dataset.label,
        "status": dataset.status,
        "rows": metadata.get("rows", ""),
        "columns": metadata.get("columns", ""),
        "planned_sites": metadata.get("planned_site_count", ""),
        "first_site": metadata.get("first_planned_site_id", ""),
        "last_site": metadata.get("last_planned_site_id", ""),
        "anchor_capture_ids": ", ".join(dataset.capture_ids),
        "overview_artifact_id": overview.id if overview is not None else "",
        "overview_status": "" if overview is None else overview.status.value,
        "warnings": _visible_grid_warning_count(session, dataset, overview, mode_registry),
    }


def _visible_overview_artifact(
    session: SessionRecord,
    artifact_id: str,
    mode_registry: ModeRegistry | None,
) -> ArtifactRecord | None:
    artifact = (session.artifacts or {}).get(artifact_id) if artifact_id else None
    if artifact is None or not artifact_visible_for_session(session, artifact, mode_registry):
        return None
    return artifact


def _visible_grid_warning_count(
    session: SessionRecord,
    dataset: GridDatasetRecord,
    overview: ArtifactRecord | None,
    mode_registry: ModeRegistry | None,
) -> int:
    warning_ids = set(dataset.warning_ids)
    if overview is not None:
        warning_ids.update(overview.warning_ids)
    warnings = {warning.id: warning for warning in session.warnings}
    return sum(
        1
        for warning_id in warning_ids
        if warning_id in warnings
        and warning_visible_for_session(session, warnings[warning_id], mode_registry)
    )
