"""KLayout-backed geometry extraction for process planning fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.process import LayerReference, MaskInterval
from metrology_process_planner.infrastructure.klayout.plugin import import_pya


@dataclass(frozen=True)
class KLayoutExtractionWarning:
    """Structured warning from KLayout geometry extraction."""

    code: str
    message: str
    cell_name: str = ""
    layer_name: str = ""


@dataclass(frozen=True)
class KLayoutLayerSummary:
    """Shape count summary for one KLayout layer in one cell."""

    layer: int
    datatype: int
    name: str
    shape_count: int


@dataclass(frozen=True)
class KLayoutCellSummary:
    """Summary of a loaded KLayout cell."""

    cell_name: str
    layer_summaries: tuple[KLayoutLayerSummary, ...]
    warnings: tuple[KLayoutExtractionWarning, ...] = ()


@dataclass(frozen=True)
class KLayoutMaskExtraction:
    """Mask intervals extracted from a KLayout cell cutline."""

    cell_name: str
    layer: LayerReference
    y: float
    intervals: tuple[MaskInterval, ...]
    warnings: tuple[KLayoutExtractionWarning, ...] = ()


class KLayoutGeometryExtractor:
    """Read GDS files through KLayout and extract process-ready masks."""

    def __init__(self, pya_module: Any | None = None) -> None:
        self._pya = pya_module

    def load_layout(self, gds_path: Path | str) -> Any:
        """Load a GDS layout with KLayout's native reader."""

        pya = self._pya_module()
        layout = pya.Layout()
        layout.read(str(gds_path))
        return layout

    def top_cell_name(self, layout: Any) -> str:
        """Return the loaded layout top-cell name."""

        top_cell = layout.top_cell()
        return "" if top_cell is None else str(top_cell.name)

    def cell_names(self, layout: Any) -> tuple[str, ...]:
        """Return loaded cell names in deterministic order."""

        names: list[str] = []
        for cell_index in layout.each_cell():
            names.append(str(cell_index.name))
        return tuple(sorted(names))

    def summarize_cell(
        self,
        layout: Any,
        cell_name: str,
        layers: tuple[LayerReference, ...],
    ) -> KLayoutCellSummary:
        """Count direct shapes for selected layers in one cell."""

        cell = layout.cell(cell_name)
        if cell is None:
            warning = KLayoutExtractionWarning(
                "KLAYOUT_CELL_MISSING",
                f"Missing cell {cell_name}.",
                cell_name,
            )
            return KLayoutCellSummary(
                cell_name,
                (),
                (warning,),
            )
        summaries = tuple(
            KLayoutLayerSummary(
                layer.layer,
                layer.datatype,
                layer.name,
                _shape_count(cell, _layer_index(layout, layer)),
            )
            for layer in layers
        )
        return KLayoutCellSummary(cell_name, summaries)

    def extract_cutline_intervals(
        self,
        layout: Any,
        cell_name: str,
        layer: LayerReference,
        y: float,
    ) -> KLayoutMaskExtraction:
        """Extract x intervals where rectangular layer geometry crosses a y cutline."""

        cell = layout.cell(cell_name)
        if cell is None:
            warning = KLayoutExtractionWarning(
                "KLAYOUT_CELL_MISSING",
                f"Missing cell {cell_name}.",
                cell_name,
                layer.name,
            )
            return KLayoutMaskExtraction(cell_name, layer, y, (), (warning,))
        layer_index = _layer_index(layout, layer)
        intervals = tuple(
            sorted(_rect_intervals(layout, cell, layer_index, y), key=lambda item: item.x_min)
        )
        warnings: tuple[KLayoutExtractionWarning, ...] = ()
        if not intervals:
            warnings = (
                KLayoutExtractionWarning(
                    "KLAYOUT_LAYER_EMPTY_AT_CUTLINE",
                    f"No {layer.name} geometry crosses y={y}.",
                    cell_name,
                    layer.name,
                ),
            )
        return KLayoutMaskExtraction(cell_name, layer, y, intervals, warnings)

    def _pya_module(self) -> Any:
        return self._pya if self._pya is not None else import_pya()


def _layer_index(layout: Any, layer: LayerReference) -> int:
    return int(layout.layer(layer.layer, layer.datatype))


def _shape_count(cell: Any, layer_index: int) -> int:
    shapes = cell.shapes(layer_index)
    return int(shapes.size())


def _rect_intervals(
    layout: Any,
    cell: Any,
    layer_index: int,
    y: float,
) -> list[MaskInterval]:
    dbu = float(layout.dbu)
    y_dbu = round(y / dbu)
    intervals: list[MaskInterval] = []
    for shape in cell.shapes(layer_index).each():
        if not shape.is_box():
            continue
        box = shape.box
        if box.bottom <= y_dbu <= box.top:
            intervals.append(MaskInterval(box.left * dbu, box.right * dbu))
    return intervals
