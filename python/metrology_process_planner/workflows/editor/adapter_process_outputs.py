"""Editor metadata and actions for process-output records."""

from __future__ import annotations

from metrology_process_planner.domains.session import ProcessOutputRecord, SessionRecord
from metrology_process_planner.rendering.cross_section.profile_defaults import (
    default_render_profile_id,
)
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import (
    EditorAction,
    EditorActionType,
    MetadataField,
)


def process_output_fields(
    session: SessionRecord,
    item: SessionItem,
    _mode_registry: object = None,
) -> tuple[MetadataField, ...]:
    """Return engineer-readable fields for a generated process output."""

    output = process_output_for_item(session, item)
    if output is None:
        return ()
    metadata = dict(output.metadata or {})
    fields = [
        MetadataField("label", "Label", output.label, read_only=True),
        MetadataField("output_type", "Output Type", output.output_type, read_only=True),
        MetadataField("status", "Status", output.status, read_only=True),
        MetadataField(
            "render_profile_id",
            "Render Profile",
            str(metadata.get("render_profile_id") or default_render_profile_id(output.output_type)),
            read_only=True,
        ),
        MetadataField("capture_id", "Capture", str(metadata.get("capture_id", "")), read_only=True),
    ]
    fields.extend(_solver_fields(metadata))
    fields.append(
        MetadataField("artifact_count", "Artifacts", str(len(output.artifact_refs or {})))
    )
    return tuple(fields)


def process_output_actions(
    session: SessionRecord,
    item: SessionItem,
    _mode_registry: object = None,
) -> tuple[EditorAction, ...]:
    """Return actions for a process-output editor item."""

    output = process_output_for_item(session, item)
    if output is None:
        return ()
    label = "Regenerate Point Stack" if output.output_type == "point_stack" else (
        "Regenerate Process Output"
    )
    return (EditorAction(EditorActionType.REGENERATE_PROCESS_OUTPUT, label, item.item_id),)


def process_output_for_item(
    session: SessionRecord,
    item: SessionItem,
) -> ProcessOutputRecord | None:
    """Return the process output referenced by an editor item."""

    if item.record_ref is None or item.record_ref.record_type != "process_output":
        return None
    for output in session.process_outputs:
        if output.id == item.record_ref.record_id:
            return output
    return None


def capture_id_for_process_output(session: SessionRecord, output_id: str) -> str:
    """Return the owning capture id for a process output id."""

    for output in session.process_outputs:
        if output.id == output_id:
            return str(dict(output.metadata or {}).get("capture_id", ""))
    return ""


def _solver_fields(metadata: dict[str, object]) -> list[MetadataField]:
    keys = (
        ("solver_backend", "Solver"),
        ("frame_count", "Frames"),
        ("cutline_sample_count", "Cutline Samples"),
        ("point_stack_count", "Point Stack Samples"),
        ("diagnostic_count", "Diagnostics"),
    )
    return [
        MetadataField(key, label, str(metadata[key]), read_only=True)
        for key, label in keys
        if key in metadata
    ]
