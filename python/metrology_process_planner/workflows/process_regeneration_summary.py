"""Solver-result summaries stored in process output records."""

from __future__ import annotations

from typing import Any

from metrology_process_planner.domains.process import SolverResult


def result_metadata(result: SolverResult) -> dict[str, Any]:
    """Return compact solver metadata for a process output record."""

    return {
        "solver_backend": "HybridCrossSectionSolver",
        "variant_label": result.variant_label,
        "frame_count": len(result.frames),
        "diagnostic_codes": [diagnostic.code for diagnostic in result.diagnostics],
        "point_sample_count": len(result.point_samples),
        "cutline_sample_count": len(result.cutline_samples),
        "snapshot_count": len(result.snapshots),
    }


def result_summary(result: SolverResult) -> dict[str, Any]:
    """Return a JSON-safe solver summary for session persistence."""

    return {
        "frames": [frame.step_id for frame in result.frames],
        "diagnostics": [
            {
                "severity": item.severity,
                "code": item.code,
                "step_id": item.step_id,
                "message": item.message,
                "output_usable": item.output_usable,
            }
            for item in result.diagnostics
        ],
        "point_stacks": [
            {"x": sample.x, "materials": [item.material_id for item in sample.intervals]}
            for sample in result.point_samples
        ],
        "cutline_sample_count": len(result.cutline_samples),
    }
