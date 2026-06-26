"""Capture geometry and canvas domain namespace."""

from metrology_process_planner.domains.capture.canvas import (
    CanvasObject,
    CanvasObjectType,
    CanvasVisualFlag,
    CanvasWorkflowState,
    PendingCapture,
    SourceViewBinding,
)
from metrology_process_planner.domains.capture.capture_features import (
    normalized_feature_payload,
)
from metrology_process_planner.domains.capture.capture_geometry import (
    CaptureGeometry,
    GeometryKind,
)
from metrology_process_planner.domains.capture.capture_geometry_validation import (
    validate_box_geometry,
    validate_feature_geometry,
    validate_line_geometry,
)
from metrology_process_planner.domains.capture.captures import CaptureRecord
from metrology_process_planner.domains.capture.grids import GridDatasetRecord

__all__ = [
    "CanvasObject",
    "CanvasObjectType",
    "CanvasVisualFlag",
    "CanvasWorkflowState",
    "CaptureGeometry",
    "CaptureRecord",
    "GeometryKind",
    "GridDatasetRecord",
    "PendingCapture",
    "SourceViewBinding",
    "normalized_feature_payload",
    "validate_box_geometry",
    "validate_feature_geometry",
    "validate_line_geometry",
]
