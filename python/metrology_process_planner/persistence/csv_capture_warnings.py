"""Warning aggregation helpers for capture CSV rows."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.artifacts.artifact_query import artifacts_for_owner
from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)


def capture_warning_count(
    session: SessionRecord,
    capture: Any,
    mode_registry: ModeRegistry | None = None,
) -> int:
    """Return open warnings linked to a capture, its measurements, or artifacts."""

    warning_ids = _visible_warning_ids(session, set(capture.warning_ids), mode_registry)
    artifact_ids = _visible_artifact_ref_ids(
        session,
        set(dict(capture.artifact_refs or {}).values()),
        mode_registry,
    )
    artifact_ids.update(_visible_owned_artifact_ids(session, "capture", capture.id, mode_registry))
    item_refs = {f"capture:{capture.id}"}
    for measurement in capture.measurements:
        _add_measurement_refs(
            session,
            measurement,
            warning_ids,
            artifact_ids,
            item_refs,
            mode_registry,
        )
    warning_ids.update(
        _visible_warning_ids(
            session,
            _artifact_warning_ids(session, artifact_ids, mode_registry),
            mode_registry,
        )
    )
    warning_ids.update(_related_warning_ids(session, item_refs, artifact_ids, mode_registry))
    return len(warning_ids)


def _visible_warning_ids(
    session: SessionRecord,
    warning_ids: set[str],
    mode_registry: ModeRegistry | None,
) -> set[str]:
    warnings_by_id = {warning.id: warning for warning in session.warnings}
    return {
        warning_id
        for warning_id in warning_ids
        if warning_id not in warnings_by_id
        or warning_visible_for_session(session, warnings_by_id[warning_id], mode_registry)
    }


def _artifact_warning_ids(
    session: SessionRecord,
    artifact_ids: set[str],
    mode_registry: ModeRegistry | None,
) -> set[str]:
    artifacts = session.artifacts or {}
    return {
        warning_id
        for artifact_id in artifact_ids
        if _artifact_visible(session, artifact_id, mode_registry)
        for warning_id in artifacts[artifact_id].warning_ids
    }


def _related_warning_ids(
    session: SessionRecord,
    item_refs: set[str],
    artifact_ids: set[str],
    mode_registry: ModeRegistry | None,
) -> set[str]:
    return {
        warning.id
        for warning in session.warnings
        if warning.status == "open"
        and warning_visible_for_session(session, warning, mode_registry)
        and _warning_related(warning, item_refs, artifact_ids)
    }


def _add_measurement_refs(
    session: SessionRecord,
    measurement: Any,
    warning_ids: set[str],
    artifact_ids: set[str],
    item_refs: set[str],
    mode_registry: ModeRegistry | None,
) -> None:
    warning_ids.update(_visible_warning_ids(session, set(measurement.warning_ids), mode_registry))
    artifact_ids.update(
        _visible_artifact_ref_ids(
            session,
            set(dict(measurement.artifact_refs or {}).values()),
            mode_registry,
        )
    )
    artifact_ids.update(
        _visible_owned_artifact_ids(session, "measurement", measurement.id, mode_registry)
    )
    item_refs.add(f"measurement:{measurement.id}")


def _visible_owned_artifact_ids(
    session: SessionRecord,
    owner_type: str,
    owner_id: str,
    mode_registry: ModeRegistry | None,
) -> set[str]:
    return {
        artifact.id
        for artifact in artifacts_for_owner(session.artifacts or {}, owner_type, owner_id)
        if artifact_visible_for_session(session, artifact, mode_registry)
    }


def _visible_artifact_ref_ids(
    session: SessionRecord,
    artifact_ids: set[str],
    mode_registry: ModeRegistry | None,
) -> set[str]:
    return {
        artifact_id
        for artifact_id in artifact_ids
        if _artifact_visible(session, artifact_id, mode_registry)
    }


def _artifact_visible(
    session: SessionRecord,
    artifact_id: str,
    mode_registry: ModeRegistry | None,
) -> bool:
    artifacts = session.artifacts or {}
    return artifact_id in artifacts and artifact_visible_for_session(
        session,
        artifacts[artifact_id],
        mode_registry,
    )


def _warning_related(warning: Any, item_refs: set[str], artifact_ids: set[str]) -> bool:
    return bool(
        item_refs.intersection(warning.related_item_refs)
        or artifact_ids.intersection(warning.related_artifact_refs)
    )
