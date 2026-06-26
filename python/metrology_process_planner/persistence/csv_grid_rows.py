"""Grid planned-site rows for recipe-free CSV exports."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import (
    GridDatasetRecord,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)
from metrology_process_planner.persistence.csv_capture_schema import CAPTURE_SUMMARY_FIELDS


def grid_site_rows(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> list[dict[str, Any]]:
    """Return one CSV row for each planned site in every grid dataset."""

    rows: list[dict[str, Any]] = []
    for dataset in session.grid_datasets:
        for index, site in enumerate(_planned_sites(dataset), start=1):
            rows.append(_grid_site_row(session, dataset, site, index, mode_registry))
    return rows


def _grid_site_row(
    session: SessionRecord,
    dataset: GridDatasetRecord,
    site: dict[str, Any],
    index: int,
    mode_registry: ModeRegistry | None,
) -> dict[str, Any]:
    center = dict(site.get("center", {}))
    overview = _overview_artifact(session, dataset, mode_registry)
    row = _empty_capture_columns(session)
    row.update(
        {
            "row_kind": "grid_site",
            "capture_id": _site_id(dataset, site, index),
            "label": _site_label(dataset, site),
            "role": "grid_site",
            "type": "planned_site",
            "status": dataset.status,
            "geometry_kind": "point",
            "center_x": center.get("x", ""),
            "center_y": center.get("y", ""),
            "grid_dataset_id": dataset.id,
            "grid_dataset_label": dataset.label,
            "grid_site_index": str(index),
            "grid_row": str(site.get("row", "")),
            "grid_column": str(site.get("column", "")),
            "grid_center_x": center.get("x", ""),
            "grid_center_y": center.get("y", ""),
            "grid_anchor_capture_ids": ";".join(dataset.capture_ids),
            "grid_overview_artifact_id": overview.id if overview is not None else "",
            "grid_overview_artifact_path": (
                overview.relative_path if overview is not None else ""
            ),
            "grid_overview_artifact_status": (
                overview.status.value if overview is not None else ""
            ),
            "artifact_statuses": (
                f"{overview.owner.role}:{overview.status.value}"
                if overview is not None
                else ""
            ),
            "warning_count": str(
                _grid_warning_count(session, dataset, overview, mode_registry)
            ),
        }
    )
    return row


def _site_id(dataset: GridDatasetRecord, site: dict[str, Any], index: int) -> str:
    return str(site.get("id") or f"{dataset.id}:site-{index:03d}")


def _site_label(dataset: GridDatasetRecord, site: dict[str, Any]) -> str:
    if site.get("label"):
        return str(site["label"])
    return f"{dataset.label} R{site.get('row', '')}C{site.get('column', '')}"


def _empty_capture_columns(session: SessionRecord) -> dict[str, Any]:
    row: dict[str, Any] = dict.fromkeys(CAPTURE_SUMMARY_FIELDS, "")
    row.update(
        {
            "session_id": session.id,
            "session_name": session.name,
            "session_mode": session.mode.value,
            "mode_id": session.mode.value,
            "coordinate_mode": session.setup.coordinate_mode,
            "units": session.coordinates.units,
            "source_layout_path": session.source_layout.layout_path,
            "source_layout_file": session.source_layout.layout_name,
            "top_cell": session.source_layout.top_cell,
            "warning_count": "0",
        }
    )
    return row


def _planned_sites(dataset: GridDatasetRecord) -> tuple[dict[str, Any], ...]:
    sites = dict(dataset.extensions or {}).get("planned_sites", ())
    if not isinstance(sites, tuple):
        sites = tuple(sites) if isinstance(sites, list) else ()
    return tuple(dict(site) for site in sites if isinstance(site, dict))


def _overview_artifact(
    session: SessionRecord,
    dataset: GridDatasetRecord,
    mode_registry: ModeRegistry | None,
) -> Any:
    artifact_id = dict(dataset.artifact_refs or {}).get("grid_overview")
    artifact = (session.artifacts or {}).get(str(artifact_id)) if artifact_id else None
    if artifact is None or not artifact_visible_for_session(session, artifact, mode_registry):
        return None
    return artifact


def _grid_warning_count(
    session: SessionRecord,
    dataset: GridDatasetRecord,
    overview: Any,
    mode_registry: ModeRegistry | None,
) -> int:
    warning_ids = set(dataset.warning_ids)
    if overview is not None:
        warning_ids.update(overview.warning_ids)
    warnings = {warning.id: warning for warning in session.warnings}
    return sum(
        1
        for warning_id in warning_ids
        if warning_id not in warnings
        or warning_visible_for_session(session, warnings[warning_id], mode_registry)
    )
