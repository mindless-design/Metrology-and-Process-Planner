"""Deterministic geometry data for the Process Planner synthetic testchip."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LayerDef:
    """Stable testchip layer definition."""

    layer: int
    datatype: int
    name: str
    purpose: str


@dataclass(frozen=True)
class Rect:
    """One deterministic rectangular layout shape in microns."""

    structure: str
    layer_name: str
    name: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float


LAYERS = (
    LayerDef(1, 0, "ACTIVE", "active silicon and field shapes"),
    LayerDef(2, 0, "POLY", "line-space and gate-like structures"),
    LayerDef(3, 0, "CONTACT", "via openings and contact cuts"),
    LayerDef(4, 0, "METAL1", "metal line features"),
    LayerDef(5, 0, "METAL2", "upper metal and overlap tests"),
    LayerDef(6, 0, "VIA", "via stack openings"),
    LayerDef(7, 0, "TRENCH", "trench and directional etch masks"),
    LayerDef(8, 0, "LINER_TEST", "conformal liner challenge geometry"),
    LayerDef(9, 0, "CMP_DENSITY", "CMP density-window structures"),
    LayerDef(10, 0, "ALIGN", "alignment and grid anchors"),
    LayerDef(11, 0, "GRID", "site array capture geometry"),
    LayerDef(12, 0, "FIB_CUT_TEST", "FIB full-stack cut targets"),
    LayerDef(13, 0, "PROFILE_TEST", "profilometry surface targets"),
    LayerDef(14, 0, "POINT_STACK_TEST", "ellipsometry point-stack targets"),
    LayerDef(15, 0, "LABEL_STRESS_TEST", "dense labels and leader stress"),
)


def rectangles() -> tuple[Rect, ...]:
    """Return all deterministic testchip rectangles."""

    try:
        from tests.fixtures.gds import process_planner_testchip_groups as groups
    except ModuleNotFoundError:
        import process_planner_testchip_groups as groups

    rects: list[Rect] = []
    for builder in (
        groups.line_space,
        groups.trench_via,
        groups.undercut,
        groups.liner,
        groups.cmp,
        groups.profilometry,
        groups.fib,
        groups.point_stack,
        groups.label_stress,
        groups.grid,
    ):
        rects.extend(builder())
    return tuple(rects)
