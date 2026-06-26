"""Build process-output requests and solver inputs from saved captures."""

from __future__ import annotations

from dataclasses import dataclass, replace

from metrology_process_planner.domains.process import (
    ProcessRecipe,
    SolverInput,
    SolverOptions,
)
from metrology_process_planner.domains.session import (
    CaptureRecord,
    ProcessContext,
    SessionRecord,
    session_mode_value,
)
from metrology_process_planner.workflows.process_capture_extensions import process_solver_request
from metrology_process_planner.workflows.process_solver_inputs import normalized_recipe

_ROLE_BY_OPERATION = {
    "point_stack": ("stack_image", "point_stack_table"),
    "line_profile": ("profile_image", "cross_section_image"),
    "full_stack_compressed": ("full_stack_compressed_image",),
    "process_flow_frames": ("process_flow_frame",),
}
_RENDER_PROFILE_BY_OPERATION = {
    "point_stack": "point_stack_schematic",
    "line_profile": "profilometry_surface_profile",
    "full_stack_compressed": "fib_full_stack_compressed",
    "process_flow_frames": "process_flow_frame",
}
_OPERATION_BY_CAPTURE_TYPE = {
    "site_plus_point": "point_stack",
    "site_plus_line": "line_profile",
    "fib_site_line": "full_stack_compressed",
    "process_flow_line": "process_flow_frames",
}
_OPERATION_BY_MODE = {
    "ellipsometry_planner": "point_stack",
    "profilometry_planner": "line_profile",
    "fib_cut_planner": "full_stack_compressed",
    "fib_planning": "full_stack_compressed",
    "process_flow_summary": "process_flow_frames",
}
_DEFAULT_CONTEXT_RENDER_PROFILES = {"", "default_cross_section"}


@dataclass(frozen=True)
class ProcessOutputRequest:
    """Normalized request for one capture-owned process output."""

    capture_id: str
    operation: str
    geometry_kind: str
    render_profile: str
    output_roles: tuple[str, ...]
    process_window_variant: str = "target"
    warning_ids: tuple[str, ...] = ()


class SolverInputBuilder:
    """Build solver inputs from canonical session/capture/process context state."""

    def build_request(
        self,
        session: SessionRecord,
        capture: CaptureRecord,
    ) -> ProcessOutputRequest:
        """Return the normalized process-output request for a saved capture."""

        request = process_solver_request(capture)
        operation = str(request.get("operation", "")) or self._operation_from_policy(
            session,
            capture,
        )
        render_profile = str(request.get("render_profile", "")) or _render_profile(
            operation,
            session.process_context,
        )
        process_window = str(
            request.get(
                "process_window_variant",
                session.process_context.process_window_variant or "target",
            )
        )
        return ProcessOutputRequest(
            capture.id,
            operation,
            _geometry_kind(operation),
            render_profile,
            _ROLE_BY_OPERATION.get(operation, ("process_output_manifest",)),
            process_window,
        )

    def build(
        self,
        session: SessionRecord,
        capture: CaptureRecord,
        recipe: ProcessRecipe,
    ) -> SolverInput:
        """Return a solver input for a capture and attached recipe."""

        process_request = self.build_request(session, capture)
        self.validate(session, capture, process_request)
        bounds = capture.geometry.bounds
        x_min = bounds.left if bounds is not None else 0.0
        x_max = bounds.right if bounds is not None else 10.0
        options = SolverOptions(x_min=x_min, x_max=x_max, sample_count=101)
        feature = capture.geometry.features[0] if capture.geometry.features else {}
        geometry = dict(feature.get("geometry", {}))
        if process_request.operation == "point_stack":
            point = dict(geometry.get("point", {}))
            options = replace(
                options,
                point_sample_xs=(float(point.get("x", (x_min + x_max) / 2)),),
            )
        if process_request.operation in {
            "line_profile",
            "full_stack_compressed",
            "process_flow_frames",
        }:
            start = dict(geometry.get("start", {}))
            end = dict(geometry.get("end", {}))
            start_x = float(start.get("x", x_min))
            end_x = float(end.get("x", x_max))
            options = replace(
                options,
                cutline_x_min=min(start_x, end_x),
                cutline_x_max=max(start_x, end_x),
            )
        return SolverInput(normalized_recipe(recipe), options)

    def validate(
        self,
        session: SessionRecord,
        capture: CaptureRecord,
        request: ProcessOutputRequest | None = None,
    ) -> None:
        """Validate that a capture can build the requested solver input."""

        process_request = request or self.build_request(session, capture)
        _validate_operation(process_request)
        _validate_parent_geometry(capture)
        _validate_child_feature(capture, process_request)

    def _operation_from_policy(self, session: SessionRecord, capture: CaptureRecord) -> str:
        if capture.type in _OPERATION_BY_CAPTURE_TYPE:
            operation = _OPERATION_BY_CAPTURE_TYPE[capture.type]
            if (
                operation == "line_profile"
                and session_mode_value(session.mode) == "process_flow_summary"
            ):
                return "process_flow_frames"
            return operation
        return _OPERATION_BY_MODE.get(session_mode_value(session.mode), "process_output")


def _render_profile(operation: str, context: ProcessContext) -> str:
    if context.render_profile not in _DEFAULT_CONTEXT_RENDER_PROFILES:
        return context.render_profile
    return _RENDER_PROFILE_BY_OPERATION.get(operation, "")


def _geometry_kind(operation: str) -> str:
    if operation == "point_stack":
        return "point"
    if operation in {"line_profile", "full_stack_compressed", "process_flow_frames"}:
        return "line"
    return "unknown"


def _validate_operation(request: ProcessOutputRequest) -> None:
    if not request.operation or request.operation == "process_output":
        raise ValueError("Process output operation is not defined for this capture.")
    if request.operation not in _ROLE_BY_OPERATION:
        raise ValueError(f"Unsupported process output operation: {request.operation}")


def _validate_parent_geometry(capture: CaptureRecord) -> None:
    if capture.geometry.bounds is None and capture.geometry.kind.value == "composite":
        raise ValueError("Composite process output requires parent site geometry.")


def _validate_child_feature(capture: CaptureRecord, request: ProcessOutputRequest) -> None:
    if request.geometry_kind == "point" and not _feature_geometry(capture, "point"):
        raise ValueError("Point-stack output requires a child point feature.")
    if request.geometry_kind == "line" and not _feature_geometry(capture, "line"):
        raise ValueError("Line-based process output requires a child line feature.")


def _feature_geometry(capture: CaptureRecord, kind: str) -> dict[str, object]:
    for feature in capture.geometry.features:
        feature_kind = str(feature.get("kind", ""))
        role = str(feature.get("role", ""))
        if feature_kind != kind and kind not in role:
            continue
        geometry = feature.get("geometry", {})
        return dict(geometry) if isinstance(geometry, dict) else {}
    return {}
