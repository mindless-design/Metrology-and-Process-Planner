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
from metrology_process_planner.domains.session.display_units import (
    DisplayUnitPreferences,
    resolved_display_unit,
)
from metrology_process_planner.domains.warnings.warning_visibility import (
    warning_visible_for_session,
)
from metrology_process_planner.persistence.csv_capture_schema import CAPTURE_SUMMARY_FIELDS
from metrology_process_planner.persistence.csv_units import convert_optional_length


def grid_site_rows(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
    display_preferences: DisplayUnitPreferences | None = None,
) -> list[dict[str, Any]]:
    """Return one CSV row for each planned site in every grid dataset."""

    rows: list[dict[str, Any]] = []
    for dataset in session.grid_datasets:
        for index, site in enumerate(_planned_sites(dataset), start=1):
            rows.append(
                _grid_site_row(
                    session,
                    dataset,
                    site,
                    index,
                    mode_registry,
                    display_preferences,
                )
            )
    return rows


def _grid_site_row(
    session: SessionRecord,
    dataset: GridDatasetRecord,
    site: dict[str, Any],
    index: int,
    mode_registry: ModeRegistry | None,
    display_preferences: DisplayUnitPreferences | None,
) -> dict[str, Any]:
    center = dict(site.get("center", {}))
    canonical_unit = str(center.get("units", session.coordinates.units))
    display_unit = _display_unit(center.get("x"), canonical_unit, display_preferences)
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
            "center_x": _convert_optional(center.get("x", ""), canonical_unit, display_unit),
            "center_y": _convert_optional(center.get("y", ""), canonical_unit, display_unit),
            "grid_dataset_id": dataset.id,
            "grid_dataset_label": dataset.label,
            "grid_site_index": str(index),
            "grid_row": str(site.get("row", "")),
            "grid_column": str(site.get("column", "")),
            "grid_center_x": _convert_optional(center.get("x", ""), canonical_unit, display_unit),
            "grid_center_y": _convert_optional(center.get("y", ""), canonical_unit, display_unit),
            "grid_anchor_capture_ids": ";".join(dataset.capture_ids),
            **_overview_columns(overview),
            "warning_count": str(
                _grid_warning_count(session, dataset, overview, mode_registry)
            ),
        }
    )
    row["units"] = display_unit
    return row


def _site_id(dataset: GridDatasetRecord, site: dict[str, Any], index: int) -> str:
    return str(site.get("id") or f"{dataset.id}:site-{index:03d}")


def _site_label(dataset: GridDatasetRecord, site: dict[str, Any]) -> str:
    if site.get("label"):
        return str(site["label"])
    return f"{dataset.label} R{site.get('row', '')}C{site.get('column', '')}"


def _overview_columns(overview: Any) -> dict[str, str]:
    if overview is None:
        return {
            "grid_overview_artifact_id": "",
            "grid_overview_artifact_path": "",
            "grid_overview_artifact_status": "",
            "artifact_statuses": "",
        }
    return {
        "grid_overview_artifact_id": overview.id,
        "grid_overview_artifact_path": overview.relative_path,
        "grid_overview_artifact_status": overview.status.value,
        "artifact_statuses": f"{overview.owner.role}:{overview.status.value}",
    }


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


def _display_unit(
    representative_value: object,
    canonical_unit: str,
    preferences: DisplayUnitPreferences | None,
) -> str:
    value = (
        float(representative_value)
        if isinstance(representative_value, (int, float, str)) and representative_value != ""
        else None
    )
    preference = preferences.layout_geometry if preferences is not None else "auto"
    return resolved_display_unit(value, canonical_unit, preference)


def _convert_optional(value: Any, canonical_unit: str, display_unit: str) -> Any:
    return convert_optional_length(value, canonical_unit, display_unit)


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
