"""Advanced process-geometry kernel facade.

The current implementation uses the sampled adaptive-column backend and exposes
advanced process metadata for render projection. It intentionally avoids a large
geometry dependency while keeping a stable replacement point for a future raster
or level-set backend.
"""

from __future__ import annotations

from metrology_process_planner.solver.sampled_geometry_kernel import SampledGeometryKernel


class AdvancedGeometryKernel(SampledGeometryKernel):
    """Deterministic advanced geometry kernel used by Process Planner."""
