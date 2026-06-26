"""Feature filtering stage for cross-section render intents."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.process import (
    Material,
    MaterialInterval,
    StackColumn,
    StackGeometry2D,
    SurfaceProfile,
)
from metrology_process_planner.rendering.cross_section.models import RenderIntent, RenderProfile


@dataclass(frozen=True)
class FilterDiagnostics:
    """Structured filtering diagnostics used by scenes and artifacts."""

    code: str
    message: str
    severity: str = "info"


@dataclass(frozen=True)
class FilteredFeatureSet:
    """Selected or relevant feature identifiers for the render."""

    selected_site_id: str = ""
    selected_feature_id: str = ""
    selected_process_step_id: str = ""
    highlighted_material_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FilteredStackGeometry:
    """Solver geometry after render-intent filtering."""

    geometry: StackGeometry2D
    surface: SurfaceProfile
    features: FilteredFeatureSet
    diagnostics: tuple[FilterDiagnostics, ...] = ()
    hidden_materials_affect_height: bool = False
    filtered_buried_detail: bool = False


class FeatureFilter:
    """Filter solver stack geometry without mutating physical truth."""

    def filter(
        self,
        geometry: StackGeometry2D,
        intent: RenderIntent,
        profile: RenderProfile,
        materials: tuple[Material, ...] = (),
    ) -> FilteredStackGeometry:
        """Return render-relevant geometry and diagnostics for one intent."""

        hidden = _hidden_material_ids(materials)
        diagnostics: list[FilterDiagnostics] = []
        if not geometry.columns:
            diagnostics.append(_empty_geometry_diagnostic())
        hidden_affects_height = _hidden_affects_height(geometry, hidden)
        if hidden_affects_height:
            diagnostics.append(
                FilterDiagnostics(
                    "RENDER_HIDDEN_MATERIALS_AFFECT_HEIGHT",
                    "Hidden materials were excluded visually but still affect stack height.",
                )
            )
        if (
            intent.focus_policy == "surface_topography"
            or profile.feature_filter_policy == "surface_topography"
        ):
            return _surface_topography_result(
                geometry,
                intent,
                tuple(diagnostics),
                hidden_affects_height,
            )
        if intent.stack_inclusion_policy == "include_visible_materials" and hidden:
            return FilteredStackGeometry(
                _without_materials(geometry, hidden),
                geometry.surface,
                _features(intent),
                tuple(diagnostics),
                hidden_affects_height,
            )
        return FilteredStackGeometry(
            geometry,
            geometry.surface,
            _features(intent),
            tuple(diagnostics),
            hidden_affects_height,
        )


def _empty_geometry_diagnostic() -> FilterDiagnostics:
    return FilterDiagnostics(
        "RENDER_FEATURE_FILTER_EMPTY",
        "No stack columns to render.",
        "warning",
    )


def _surface_topography_result(
    geometry: StackGeometry2D,
    intent: RenderIntent,
    diagnostics: tuple[FilterDiagnostics, ...],
    hidden_affects_height: bool,
) -> FilteredStackGeometry:
    filtered_diagnostics = diagnostics + (
        FilterDiagnostics(
            "RENDER_BURIED_DETAIL_FILTERED",
            "Profilometry render filtered buried detail that does not affect surface.",
        ),
    )
    return FilteredStackGeometry(
        _surface_topography_geometry(geometry),
        geometry.surface,
        _features(intent),
        filtered_diagnostics,
        hidden_affects_height,
        filtered_buried_detail=True,
    )


def _surface_topography_geometry(geometry: StackGeometry2D) -> StackGeometry2D:
    columns = tuple(_surface_column(column) for column in geometry.columns)
    return StackGeometry2D(columns)


def _surface_column(column: StackColumn) -> StackColumn:
    if not column.intervals:
        return column
    top = max(column.intervals, key=lambda item: item.z_max)
    thickness = max(0.0, top.z_max - top.z_min)
    context = max(min(thickness, 50.0), min(10.0, thickness or 10.0))
    interval = MaterialInterval(top.material_id, top.z_max - context, top.z_max)
    return StackColumn(column.x, (interval,))


def _without_materials(geometry: StackGeometry2D, material_ids: set[str]) -> StackGeometry2D:
    columns = tuple(
        StackColumn(
            column.x,
            tuple(interval for interval in column.intervals
                  if interval.material_id not in material_ids),
        )
        for column in geometry.columns
    )
    return StackGeometry2D(columns)


def _hidden_material_ids(materials: tuple[Material, ...]) -> set[str]:
    return {material.id for material in materials if not material.visible}


def _hidden_affects_height(geometry: StackGeometry2D, hidden: set[str]) -> bool:
    for column in geometry.columns:
        if not column.intervals:
            continue
        top = max(column.intervals, key=lambda item: item.z_max)
        if top.material_id in hidden:
            return True
    return False


def _features(intent: RenderIntent) -> FilteredFeatureSet:
    return FilteredFeatureSet(
        intent.selected_site_id,
        intent.selected_feature_id,
        intent.selected_process_step_id or "",
        (),
    )
