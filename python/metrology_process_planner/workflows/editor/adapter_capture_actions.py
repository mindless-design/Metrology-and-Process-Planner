"""Saved-capture editor action policy."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    CaptureRecord,
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
)
from metrology_process_planner.workflows.editor.adapter_artifact_actions import (
    artifact_repair_actions,
)
from metrology_process_planner.workflows.editor.adapter_measurement_policy import (
    mode_supports_measurements,
)
from metrology_process_planner.workflows.editor.adapter_process import (
    process_context_actions,
)
from metrology_process_planner.workflows.editor.adapter_visual_actions import (
    visual_artifact_actions,
)
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType
from metrology_process_planner.workflows.measurement_workflow import (
    measurement_parent_unavailable_reason,
)


def saved_capture_actions(
    session: SessionRecord,
    item: SessionItem,
    mode_registry: ModeRegistry | None = None,
) -> tuple[EditorAction, ...]:
    """Return actions for a saved capture from canonical capture data."""

    capture = _capture_by_item(session, item)
    if capture is None:
        return _generic_capture_actions(session, item, None, mode_registry)
    feature_label = _first_feature_label(capture)
    if feature_label:
        return _site_plus_feature_actions(
            session,
            item,
            feature_label,
            _process_label(capture),
            mode_registry,
        )
    return _generic_capture_actions(session, item, capture, mode_registry)


def _site_plus_feature_actions(
    session: SessionRecord,
    item: SessionItem,
    feature_label: str,
    process_label: str,
    mode_registry: ModeRegistry | None,
) -> tuple[EditorAction, ...]:
    actions = _metadata_copy_actions(item) + (
        EditorAction(EditorActionType.REPLACE_SITE_BOX, "Replace Site Box", item.item_id),
        EditorAction(
            EditorActionType.REPLACE_INNER_FEATURE,
            f"Replace {feature_label}",
            item.item_id,
            payload=(("feature_kind", feature_label.lower()),),
        ),
        *_measurement_actions(session, item, _capture_by_item(session, item), mode_registry),
        *artifact_repair_actions(item, f"Regenerate {feature_label} Annotation"),
        *visual_artifact_actions(item),
    )
    if not _mode_is_process_aware(session, mode_registry):
        return actions
    return actions + process_context_actions(item.item_id) + (
        EditorAction(
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
            process_label,
            item.item_id,
        ),
    )


def _generic_capture_actions(
    session: SessionRecord,
    item: SessionItem,
    capture: CaptureRecord | None,
    mode_registry: ModeRegistry | None,
) -> tuple[EditorAction, ...]:
    actions = _metadata_copy_actions(item) + (
        EditorAction(
            EditorActionType.REPLACE_SITE_BOX,
            "Replace Capture",
            item.item_id,
            enabled=capture is not None and capture.geometry.bounds is not None,
            disabled_reason=(
                "" if capture is not None and capture.geometry.bounds is not None
                else "Only saved box captures can be replaced."
            ),
        ),
        *_measurement_actions(session, item, capture, mode_registry),
        *artifact_repair_actions(item, "Regenerate Image"),
        *visual_artifact_actions(item),
    )
    if not _mode_is_process_aware(session, mode_registry):
        return actions
    return actions + process_context_actions(item.item_id) + (
        EditorAction(
            EditorActionType.REGENERATE_PROCESS_OUTPUT,
            "Regenerate Process Output",
            item.item_id,
        ),
    )


def _metadata_copy_actions(item: SessionItem) -> tuple[EditorAction, ...]:
    return (
        EditorAction(EditorActionType.EDIT_METADATA, "Edit Metadata", item.item_id),
        EditorAction(
            EditorActionType.COPY_CENTER_COORDINATE,
            "Copy Center Coordinate",
            item.item_id,
        ),
        EditorAction(EditorActionType.COPY_BOUNDS, "Copy Bounds", item.item_id),
        EditorAction(EditorActionType.COPY_CSV_ROW, "Copy CSV Row", item.item_id),
    )


def _measurement_actions(
    session: SessionRecord,
    item: SessionItem,
    capture: CaptureRecord | None,
    mode_registry: ModeRegistry | None,
) -> tuple[EditorAction, ...]:
    if not mode_supports_measurements(session, mode_registry):
        return ()
    disabled_reason = (
        "Measurements require a saved capture."
        if capture is None
        else measurement_parent_unavailable_reason(session, capture.id)
    )
    return (
        EditorAction(
            EditorActionType.ADD_MEASUREMENT,
            "Add Measurement",
            item.item_id,
            enabled=not disabled_reason,
            disabled_reason=disabled_reason,
        ),
    )


def _capture_by_item(session: SessionRecord, item: SessionItem) -> CaptureRecord | None:
    if item.record_ref is None:
        return None
    for capture in session.captures:
        if capture.id == item.record_ref.record_id:
            return capture
    return None


def _first_feature_label(capture: CaptureRecord) -> str:
    if not capture.geometry.features:
        return ""
    label = str(capture.geometry.features[0].get("label", ""))
    if label:
        return label
    kind = str(capture.geometry.features[0].get("kind", "feature"))
    return kind.replace("_", " ").title()


def _process_label(capture: CaptureRecord) -> str:
    operation = _solver_operation(capture)
    if operation == "point_stack":
        return "Regenerate Point Stack"
    return "Regenerate Process Output"


def _mode_is_process_aware(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    mode = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    return (
        mode.family == "process_aware"
        or mode.capabilities.supports_process_solver
        or mode.process.recipe_policy not in {"forbidden", "optional_hidden"}
    )


def _solver_operation(capture: CaptureRecord) -> str:
    for extension in (capture.extensions or {}).values():
        if isinstance(extension, dict):
            request = extension.get("solver_request", {})
            if isinstance(request, dict):
                return str(request.get("operation", ""))
    return ""
