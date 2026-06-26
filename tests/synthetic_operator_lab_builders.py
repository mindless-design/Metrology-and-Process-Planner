"""Synthetic operator lab session and capture builders."""

from __future__ import annotations

from metrology_process_planner.domains.capture.capture_geometry import GeometryKind
from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
    SourceLayoutContext,
)
from tests.synthetic_process_lab import GDS_ROOT, extract_structure


def base_operator_session(session_id: str) -> SessionRecord:
    """Return a deterministic process-aware synthetic session shell."""

    return SessionRecord(
        id=session_id,
        name="Synthetic Operator Lab",
        mode=SessionMode.PROCESS_AWARE_METROLOGY,
        created_at="2026-06-26T00:00:00Z",
        updated_at="2026-06-26T00:00:00Z",
        source_layout=SourceLayoutContext(
            layout_path=str(GDS_ROOT / "process_planner_testchip.gds"),
            layout_name="process_planner_testchip.gds",
            top_cell="PROCESS_PLANNER_TESTCHIP",
            layout_fingerprint="synthetic-manifest-v1",
        ),
        metadata={"operator_lab": "synthetic_e2e"},
    )


def profile_capture(capture_id: str) -> CaptureRecord:
    """Return a profilometry line capture derived from the synthetic GDS manifest."""

    snapshot = extract_structure("profilometry_surface_test")
    bounds = _bounds(snapshot.to_dict()["rectangles"])
    return _capture(
        capture_id,
        "Synthetic Profilometry Line",
        "site_plus_line",
        CaptureGeometry(
            GeometryKind.COMPOSITE,
            bounds=bounds,
            features=(
                {
                    "id": f"{capture_id}-line",
                    "role": "profile_line",
                    "kind": "line",
                    "geometry": {
                        "start": {"x": bounds.left, "y": (bounds.bottom + bounds.top) / 2},
                        "end": {"x": bounds.right, "y": (bounds.bottom + bounds.top) / 2},
                    },
                },
            ),
            metadata={"source_structure": "profilometry_surface_test", "units": "um"},
        ),
        "profilometry",
        "line_profile",
        "profilometry_surface_profile",
    )


def point_capture(capture_id: str) -> CaptureRecord:
    """Return an ellipsometry point capture derived from the synthetic GDS manifest."""

    snapshot = extract_structure("point_stack_ellipsometry")
    bounds = _bounds(snapshot.to_dict()["rectangles"])
    return _capture(
        capture_id,
        "Synthetic Ellipsometry Point",
        "site_plus_point",
        CaptureGeometry(
            GeometryKind.COMPOSITE,
            bounds=bounds,
            features=(
                {
                    "id": f"{capture_id}-point",
                    "role": "stack_point",
                    "kind": "point",
                    "geometry": {"point": bounds.center.to_dict()},
                },
            ),
            metadata={"source_structure": "point_stack_ellipsometry", "units": "um"},
        ),
        "ellipsometry",
        "point_stack",
        "point_stack_schematic",
    )


def source_artifacts() -> dict[str, ArtifactRecord]:
    """Return the deliberately missing source-layout visual artifact."""

    return {
        "source-site-image": ArtifactRecord(
            "source-site-image",
            "image",
            "Synthetic source site image",
            "images/source-site-image.png",
            ArtifactOwnerRef("capture", "cap-profile-001", "site_image"),
            status=ArtifactStatus.MISSING,
            repair=ArtifactRepairMetadata(
                "regenerate_artifact",
                "Regenerate the source layout image.",
                regenerable=True,
                requires_live_layout=True,
            ),
        )
    }


def _capture(
    capture_id: str,
    label: str,
    capture_type: str,
    geometry: CaptureGeometry,
    extension_key: str,
    operation: str,
    render_profile: str,
) -> CaptureRecord:
    return CaptureRecord(
        id=capture_id,
        label=label,
        geometry=geometry,
        created_at="2026-06-26T00:00:00Z",
        sequence=1,
        role="site",
        type=capture_type,
        artifact_refs={"site_image": "source-site-image"},
        extensions={
            extension_key: {
                "process_context_ref": "process_context.active",
                "solver_request": {
                    "operation": operation,
                    "process_window_variant": "target",
                    "render_profile": render_profile,
                },
                "status": "pending_solver",
            }
        },
    )


def _bounds(rectangles: object) -> Box:
    items = list(rectangles) if isinstance(rectangles, list) else []
    return Box(
        min(float(item["x_min"]) for item in items),
        min(float(item["y_min"]) for item in items),
        max(float(item["x_max"]) for item in items),
        max(float(item["y_max"]) for item in items),
    )
