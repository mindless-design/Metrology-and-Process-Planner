"""Stable planned-site entries for recipe-free grid measurement."""

from __future__ import annotations

from metrology_process_planner.domains.geometry import Box, Point


def planned_grid_sites(
    dataset_id: str,
    dataset_label: str,
    first_anchor: Box,
    diagonal_anchor: Box,
    rows: int,
    columns: int,
) -> tuple[dict[str, object], ...]:
    """Return row-major planned-site entries with stable IDs and labels."""

    start = first_anchor.center
    end = diagonal_anchor.center
    dx = _step(start.x, end.x, columns)
    dy = _step(start.y, end.y, rows)
    return tuple(
        _site(
            dataset_id,
            dataset_label,
            index + 1,
            row + 1,
            column + 1,
            Point(start.x + column * dx, start.y + row * dy),
        )
        for index, (row, column) in enumerate(
            (row, column) for row in range(rows) for column in range(columns)
        )
    )


def _step(start: float, end: float, count: int) -> float:
    return 0.0 if count <= 1 else (end - start) / float(count - 1)


def _site(
    dataset_id: str,
    dataset_label: str,
    sequence: int,
    row: int,
    column: int,
    center: Point,
) -> dict[str, object]:
    return {
        "id": f"{dataset_id}:site-{sequence:03d}",
        "label": f"{dataset_label} R{row:02d}C{column:02d}",
        "sequence": sequence,
        "row": row,
        "column": column,
        "center": center.to_dict(),
    }
