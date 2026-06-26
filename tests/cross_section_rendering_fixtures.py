"""Pure Python geometry fixtures for cross-section rendering tests."""

from __future__ import annotations

from metrology_process_planner.domains.process import (
    CrossSectionProfile,
    MaterialInterval,
    ProcessFrame,
    SolverResult,
    StackColumn,
)
from metrology_process_planner.domains.process.materials import material_catalog_with

MATERIAL_IDS = (
    "si",
    "oxide",
    "metal",
    "al2o3",
    "native_oxide",
    "dielectric",
)
MATERIALS = material_catalog_with(MATERIAL_IDS)


def simple_stack_result() -> SolverResult:
    """Return Si, oxide, and patterned metal line geometry."""

    return _result(
        "simple",
        (
            _column(0.0, ("si", 0.0, 1000.0), ("oxide", 1000.0, 1100.0)),
            _column(1.0, ("si", 0.0, 1000.0), ("oxide", 1000.0, 1100.0),
                    ("metal", 1100.0, 1180.0)),
        ),
    )


def conformal_liner_result() -> SolverResult:
    """Return a trench-like stack with an 8 nm conformal liner."""

    return _result(
        "conformal",
        (
            _column(0.0, ("si", 0.0, 1000.0), ("oxide", 1000.0, 1500.0),
                    ("al2o3", 1500.0, 1508.0)),
            _column(1.0, ("si", 0.0, 1000.0), ("oxide", 1000.0, 1100.0),
                    ("al2o3", 1100.0, 1108.0), ("metal", 1108.0, 1208.0)),
            _column(2.0, ("si", 0.0, 1000.0), ("oxide", 1000.0, 1500.0),
                    ("al2o3", 1500.0, 1508.0)),
        ),
    )


def profilometry_surface_result() -> SolverResult:
    """Return buried detail plus top dielectric step geometry."""

    return _result(
        "profilometry",
        (
            _column(0.0, ("si", 0.0, 1000.0), ("native_oxide", 1000.0, 1002.0),
                    ("metal", 1002.0, 1082.0), ("dielectric", 1082.0, 1200.0)),
            _column(1.0, ("si", 0.0, 1000.0), ("oxide", 1000.0, 1050.0),
                    ("metal", 1050.0, 1130.0), ("dielectric", 1130.0, 1250.0)),
        ),
    )


def fib_full_stack_result() -> SolverResult:
    """Return a full stack where substrate dominates physical height."""

    return _result(
        "fib",
        (
            _column(0.0, ("si", 0.0, 500000.0), ("oxide", 500000.0, 501000.0),
                    ("metal", 501000.0, 501080.0), ("al2o3", 501080.0, 501085.0)),
        ),
    )


def process_flow_result() -> SolverResult:
    """Return frames with one duplicate signature for changed-frame filtering."""

    frames = (
        _frame("01", "Step 01 - substrate", (_column(0.0, ("si", 0.0, 1000.0)),)),
        _frame("02", "Step 02 - oxide", (_column(0.0, ("si", 0.0, 1000.0),
                                                 ("oxide", 1000.0, 1100.0)),)),
        _frame("03", "Step 03 - unchanged", (_column(0.0, ("si", 0.0, 1000.0),
                                                    ("oxide", 1000.0, 1100.0)),)),
        _frame("04", "Step 04 - liner", (_column(0.0, ("si", 0.0, 1000.0),
                                              ("oxide", 1000.0, 1100.0),
                                              ("al2o3", 1100.0, 1108.0)),)),
    )
    return SolverResult(frames)


def _result(step_id: str, columns: tuple[StackColumn, ...]) -> SolverResult:
    return SolverResult((_frame(step_id, step_id, columns),), units="nm")


def _frame(step_id: str, title: str, columns: tuple[StackColumn, ...]) -> ProcessFrame:
    return ProcessFrame(step_id, title, CrossSectionProfile(columns))


def _column(x: float, *intervals: tuple[str, float, float]) -> StackColumn:
    return StackColumn(x, tuple(MaterialInterval(*interval) for interval in intervals))
