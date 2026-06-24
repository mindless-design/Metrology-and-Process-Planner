"""Validation reports for declarative mode definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModeCompatibilityReport:
    """Validation report for one declarative mode."""

    mode_id: str
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    unsupported_features: tuple[str, ...] = ()
    fallback_actions: tuple[str, ...] = ()

    def messages(self) -> tuple[str, ...]:
        """Return all user-facing validation messages."""

        return self.errors + self.warnings + self.unsupported_features


class ModeValidator:
    """Validate declarative mode definitions against registered platform IDs."""

    _families = {
        "generic_capture",
        "review",
        "metrology",
        "grid",
        "process_aware",
        "process_flow",
        "capture",
    }
    _primitives = {
        "site_box",
        "box_capture",
        "point",
        "point_capture",
        "line_capture",
        "site_then_point",
        "site_then_line",
        "site_then_inner_features",
        "two_anchor_grid",
        "grid",
        "measurement",
    }
    _field_types = {
        "text",
        "multiline_text",
        "enum",
        "number",
        "units_number",
        "checkbox",
        "color",
        "layer_reference",
        "recipe_reference",
        "tag_list",
    }
    _solver_operations = {
        "",
        "none",
        "point_stack",
        "line_profile",
        "full_stack_compressed",
        "process_flow_frames",
    }
    _canvas_object_types = {
        "site_box",
        "point",
        "line",
        "measurement",
        "profilometry_line",
        "ellipsometry_point",
        "cross_section",
        "profilometry",
        "fib_cut",
        "multi_line",
    }

    def validate(self, definition: Any) -> ModeCompatibilityReport:
        """Return structural and semantic validation for a mode."""

        errors = list(_required_errors(definition))
        warnings = list(_semantic_warnings(definition))
        unsupported = list(_unsupported_features(definition, self))
        return ModeCompatibilityReport(
            definition.mode_id,
            not errors and not unsupported,
            tuple(errors),
            tuple(warnings),
            tuple(unsupported),
            ("hide_mode",) if errors or unsupported else (),
        )


def _required_errors(definition: Any) -> tuple[str, ...]:
    errors: list[str] = []
    if not definition.mode_id:
        errors.append("Mode id is required.")
    if not definition.display_name:
        errors.append("Mode label is required.")
    if not definition.capture.supported_primitives:
        label = definition.mode_id or "<missing>"
        errors.append(f"Mode {label}: At least one capture primitive is required.")
    return tuple(errors)


def _semantic_warnings(definition: Any) -> tuple[str, ...]:
    warnings: list[str] = []
    capture = definition.capture
    if definition.family not in ModeValidator._families:
        warnings.append(f"Mode {definition.mode_id or '<missing>'}: unknown family.")
    if capture.primitive_type in {"site_then_line", "site_then_point"}:
        warnings.extend(_compound_warnings(definition))
    operation = definition.process.solver_operation
    if operation != "none" and definition.process.recipe_policy == "forbidden":
        warnings.append(f"Mode {definition.mode_id or '<missing>'}: solver needs recipe access.")
    return tuple(warnings)


def _compound_warnings(definition: Any) -> tuple[str, ...]:
    capture = definition.capture
    warnings: list[str] = []
    if capture.supported_primitives != (capture.primitive_type,):
        warnings.append(
            f"Mode {definition.mode_id or '<missing>'}: compound modes must declare "
            f"primitive {capture.primitive_type}."
        )
    expected = "line" if capture.primitive_type == "site_then_line" else "point"
    if capture.inner_feature_kind != expected:
        warnings.append(
            f"Mode {definition.mode_id or '<missing>'}: {capture.primitive_type} "
            f"must declare an inner {expected} feature."
        )
    warnings.extend(_compound_contract_warnings(definition))
    operation = definition.process.solver_operation
    if operation not in _solver_operations_for(expected):
        warnings.append(
            f"Mode {definition.mode_id or '<missing>'}: solver operation should match "
            f"{capture.primitive_type}."
        )
    return tuple(warnings)


def _solver_operations_for(kind: str) -> set[str]:
    common = {"", "none"}
    if kind == "line":
        return common | {"line_profile", "full_stack_compressed"}
    if kind == "point":
        return common | {"point_stack"}
    return common


def _compound_contract_warnings(definition: Any) -> tuple[str, ...]:
    capture = definition.capture
    artifact_policy = definition.artifacts
    required = {
        "saved capture type": capture.saved_capture_type,
        "extension key": capture.extension_key,
        "feature id field": capture.feature_id_field,
        "process output key": capture.process_output_key,
        "annotation artifact role": artifact_policy.annotation_role_on_capture_save(),
        "inner feature label": capture.inner_feature_label,
        "child canvas object type": capture.child_canvas_object_type,
    }
    return tuple(
        f"Mode {definition.mode_id or '<missing>'}: missing {label}."
        for label, value in required.items()
        if not value
    )


def _unsupported_features(definition: Any, validator: ModeValidator) -> tuple[str, ...]:
    unsupported: list[str] = []
    unsupported.extend(
        f"Unsupported capture primitive: {primitive}"
        for primitive in definition.capture.supported_primitives
        if primitive not in validator._primitives
    )
    unsupported.extend(
        f"Unsupported metadata field type: {field.field_type}"
        for field in definition.metadata.capture_fields
        if field.field_type not in validator._field_types
    )
    operation = definition.process.solver_operation
    if operation not in validator._solver_operations:
        unsupported.append(f"Unsupported solver operation: {operation}")
    canvas_type = definition.capture.child_canvas_object_type
    if canvas_type and canvas_type not in validator._canvas_object_types:
        unsupported.append(f"Unsupported child canvas object type: {canvas_type}")
    return tuple(unsupported)
