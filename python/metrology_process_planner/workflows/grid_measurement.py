"""Shared grid measurement planning workflow."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import (
    CaptureRecord,
    GridDatasetRecord,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import next_id
from metrology_process_planner.workflows.grid_measurement_overview import (
    clear_grid_placeholder_warning,
    grid_overview_placeholder,
    grid_overview_placeholder_warning,
    grid_overview_svg,
    present_grid_overview,
)
from metrology_process_planner.workflows.grid_planned_sites import planned_grid_sites


def create_grid_dataset(
    session: SessionRecord,
    first_anchor_capture_id: str,
    diagonal_anchor_capture_id: str,
    row_count: int,
    column_count: int,
    label: str = "",
) -> SessionRecord:
    """Create a grid dataset from two diagonal anchor captures."""

    command = _GridCommand(
        first_anchor_capture_id,
        diagonal_anchor_capture_id,
        row_count,
        column_count,
        label,
    )
    warnings = _validation_warnings(session, command)
    if warnings:
        return _with_warnings(session, warnings)
    dataset = _grid_dataset(session, command)
    warning = grid_overview_placeholder_warning(dataset)
    artifact = grid_overview_placeholder(dataset, warning.id)
    dataset = replace(
        dataset,
        artifact_refs={"grid_overview": artifact.id},
        warning_ids=(warning.id,),
    )
    grids = session.grid_datasets + (dataset,)
    artifacts = {**dict(session.artifacts or {}), artifact.id: artifact}
    return replace(
        session,
        grid_datasets=grids,
        artifacts=artifacts,
        warnings=session.warnings + (warning,),
    )


def generate_grid_dataset_overview_artifact(
    session: SessionRecord,
    dataset_id: str,
    output_folder: Path,
) -> SessionRecord:
    """Generate the dataset-owned grid overview artifact without process context."""

    dataset = _dataset_by_id(session, dataset_id)
    if dataset is None:
        return session
    artifact = present_grid_overview(dataset, grid_overview_svg(dataset), output_folder)
    warning_id = grid_overview_placeholder_warning(dataset).id
    datasets = tuple(
        clear_grid_placeholder_warning(item, warning_id)
        if item.id == dataset.id
        else item
        for item in session.grid_datasets
    )
    artifacts = dict(session.artifacts or {})
    artifacts[artifact.id] = artifact
    warnings = tuple(warning for warning in session.warnings if warning.id != warning_id)
    return replace(session, grid_datasets=datasets, artifacts=artifacts, warnings=warnings)


class _GridCommand:
    def __init__(
        self,
        first_anchor_id: str,
        diagonal_anchor_id: str,
        rows: int,
        columns: int,
        label: str,
    ) -> None:
        self.first_anchor_id = first_anchor_id
        self.diagonal_anchor_id = diagonal_anchor_id
        self.rows = rows
        self.columns = columns
        self.label = label


def _validation_warnings(
    session: SessionRecord,
    command: _GridCommand,
) -> tuple[WarningRecord, ...]:
    warnings = []
    first = _capture_by_id(session, command.first_anchor_id)
    diagonal = _capture_by_id(session, command.diagonal_anchor_id)
    if first is None or diagonal is None:
        warnings.append(
            _warning(
                "GRID_ANCHOR_MISSING",
                "Grid anchors must be saved captures.",
                _anchor_refs(command),
            )
        )
    if command.rows <= 0 or command.columns <= 0:
        warnings.append(
            _warning(
                "GRID_SIZE_INVALID",
                "Grid rows and columns must be positive.",
                _anchor_refs(command),
            )
        )
    if first is not None and diagonal is not None:
        warnings.extend(_geometry_warnings(first, diagonal))
    return tuple(warnings)


def _geometry_warnings(first: CaptureRecord, diagonal: CaptureRecord) -> tuple[WarningRecord, ...]:
    first_box = first.geometry.bounds
    diagonal_box = diagonal.geometry.bounds
    refs = (f"capture:{first.id}", f"capture:{diagonal.id}")
    if first_box is None or diagonal_box is None:
        return (_warning("GRID_ANCHOR_NOT_BOX", "Grid anchors must use box geometry.", refs),)
    if first_box.center.distance_to(diagonal_box.center) <= 0:
        return (_warning("GRID_GEOMETRY_INVALID", "Grid anchors must not overlap exactly.", refs),)
    return ()


def _grid_dataset(session: SessionRecord, command: _GridCommand) -> GridDatasetRecord:
    first = _capture_by_id(session, command.first_anchor_id)
    diagonal = _capture_by_id(session, command.diagonal_anchor_id)
    if first is None or diagonal is None or first.geometry.bounds is None:
        raise ValueError("Grid dataset creation requires valid anchor captures.")
    if diagonal.geometry.bounds is None:
        raise ValueError("Grid dataset creation requires valid anchor captures.")
    dataset_id = next_id("grid", (dataset.id for dataset in session.grid_datasets))
    label = command.label or f"Grid {dataset_id}"
    sites = planned_grid_sites(
        dataset_id,
        label,
        first.geometry.bounds,
        diagonal.geometry.bounds,
        command.rows,
        command.columns,
    )
    metadata = {
        "rows": command.rows,
        "columns": command.columns,
        "anchor_capture_ids": (command.first_anchor_id, command.diagonal_anchor_id),
        "planned_site_count": len(sites),
        "first_planned_site_id": sites[0]["id"] if sites else "",
        "last_planned_site_id": sites[-1]["id"] if sites else "",
    }
    extensions = {"planned_sites": tuple(site for site in sites)}
    return GridDatasetRecord(
        dataset_id,
        label,
        capture_ids=(command.first_anchor_id, command.diagonal_anchor_id),
        metadata=metadata,
        extensions=extensions,
    )


def _dataset_by_id(session: SessionRecord, dataset_id: str) -> GridDatasetRecord | None:
    for dataset in session.grid_datasets:
        if dataset.id == dataset_id:
            return dataset
    return None


def _capture_by_id(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    for capture in session.captures:
        if capture.id == capture_id:
            return capture
    return None


def _warning(
    code: str,
    message: str,
    related_item_refs: tuple[str, ...],
) -> WarningRecord:
    return WarningRecord(
        f"warning-{code.lower().replace('_', '-')}",
        message,
        source="grid_measurement",
        code=code,
        related_item_refs=related_item_refs,
        repair_suggestion="Review grid anchors and row/column counts.",
    )


def _anchor_refs(command: _GridCommand) -> tuple[str, ...]:
    return (
        f"capture:{command.first_anchor_id}",
        f"capture:{command.diagonal_anchor_id}",
    )


def _with_warnings(
    session: SessionRecord,
    warnings: tuple[WarningRecord, ...],
) -> SessionRecord:
    stored = {warning.id: warning for warning in session.warnings}
    stored.update({warning.id: warning for warning in warnings})
    return replace(session, warnings=tuple(stored.values()))
