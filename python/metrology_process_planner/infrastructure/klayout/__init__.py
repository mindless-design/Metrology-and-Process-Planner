"""KLayout-specific adapter boundary.

Importing this package must not require KLayout. Adapter functions import `pya`
only when called from a live KLayout runtime.
"""

from metrology_process_planner.infrastructure.klayout.geometry import (
    KLayoutCellSummary,
    KLayoutExtractionWarning,
    KLayoutGeometryExtractor,
    KLayoutLayerSummary,
    KLayoutMaskExtraction,
)

__all__ = [
    "KLayoutCellSummary",
    "KLayoutExtractionWarning",
    "KLayoutGeometryExtractor",
    "KLayoutLayerSummary",
    "KLayoutMaskExtraction",
]
