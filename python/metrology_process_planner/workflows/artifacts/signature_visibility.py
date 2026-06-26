"""Mode-aware data shaping for artifact dependency signatures."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)


def visible_session_data(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> dict[str, Any]:
    """Return session data relevant to recipe-free freshness checks."""

    all_artifact_ids = set(session.artifacts or {})
    artifacts = _visible_artifacts(session, mode_registry)
    return {
        "id": session.id,
        "name": session.name,
        "mode": session.mode.value,
        "coordinates": session.coordinates.to_dict(),
        "source_layout": session.source_layout.to_dict(),
        "captures": [
            _capture_data(capture.to_dict(), artifacts, all_artifact_ids)
            for capture in session.captures
        ],
        "grid_datasets": [
            _owner_data(dataset.to_dict(), artifacts, all_artifact_ids)
            for dataset in session.grid_datasets
        ],
        "artifacts": _artifact_data(artifacts),
        "warnings": [
            warning.to_dict()
            for warning in session.warnings
            if warning_visible_for_session(session, warning, mode_registry)
        ],
    }


def _visible_artifacts(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> dict[str, Any]:
    return {
        artifact_id: artifact
        for artifact_id, artifact in (session.artifacts or {}).items()
        if artifact.type != "csv_export"
        and artifact.owner.owner_type != "report"
        and artifact_visible_for_session(session, artifact, mode_registry)
    }


def _artifact_data(artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        artifact_id: {
            "type": artifact.type,
            "relative_path": artifact.relative_path,
            "status": artifact.status.value,
            "owner": artifact.owner.to_dict(),
        }
        for artifact_id, artifact in artifacts.items()
    }


def _capture_data(
    data: dict[str, Any],
    artifacts: dict[str, Any],
    all_artifact_ids: set[str],
) -> dict[str, Any]:
    data = _owner_data(data, artifacts, all_artifact_ids)
    data["measurements"] = [
        _owner_data(dict(measurement), artifacts, all_artifact_ids)
        for measurement in data.get("measurements", ())
    ]
    return data


def _owner_data(
    data: dict[str, Any],
    artifacts: dict[str, Any],
    all_artifact_ids: set[str],
) -> dict[str, Any]:
    data["artifact_refs"] = _visible_refs(
        dict(data.get("artifact_refs", {})),
        artifacts,
        all_artifact_ids,
    )
    return data


def _visible_refs(
    refs: dict[str, str],
    artifacts: dict[str, Any],
    all_artifact_ids: set[str],
) -> dict[str, str]:
    return {
        role: artifact_id
        for role, artifact_id in refs.items()
        if artifact_id not in all_artifact_ids or artifact_id in artifacts
    }
