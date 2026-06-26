"""Artifact regeneration action support for the editor dispatcher."""

from __future__ import annotations

from typing import Optional, Protocol

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.dispatcher_artifact_ops import (
    regenerate_capture_visual_role,
    regenerate_report_artifact,
    regenerate_setup_artifact,
)
from metrology_process_planner.workflows.editor.dispatcher_artifact_targets import (
    target_for_selected_artifact,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import _payload_value
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.render_bridge import SessionRenderBridge
from metrology_process_planner.workflows.editor.render_bridge_models import (
    CrossSectionRenderInput,
    RenderRefreshRequest,
    RenderRefreshResult,
    RenderTarget,
)
from metrology_process_planner.workflows.editor.view_models import EditorAction
from metrology_process_planner.workflows.grid_measurement import (
    generate_grid_dataset_overview_artifact,
)


class _ArtifactRenderingDispatcher(Protocol):
    """Dispatcher fields needed by artifact regeneration actions."""

    _paths: Optional[SessionPaths]
    _render_bridge: Optional[SessionRenderBridge]
    _cross_section_inputs: dict[str, CrossSectionRenderInput]
    _mode_registry: ModeRegistry | None

    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after workflow state changes."""


def regenerate_artifact(
    dispatcher: _ArtifactRenderingDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Regenerate the artifact or drawing selected in the editor."""

    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    item = document.items_by_id.get(action.item_id)
    if item is None:
        return EditorActionResult("unavailable", document, "No refreshable item is selected.")
    if item.role == "setup":
        return regenerate_setup_artifact(dispatcher, document, action)
    if item.record_ref is None:
        return EditorActionResult("unavailable", document, "No refreshable item is selected.")
    return _regenerate_record_artifact(dispatcher, document, action)


def _regenerate_record_artifact(
    dispatcher: _ArtifactRenderingDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    item = document.items_by_id[action.item_id]
    assert item.record_ref is not None
    assert dispatcher._paths is not None
    record_ref = item.record_ref
    if _is_capture_visual_role(record_ref.record_type, _payload_value(action, "role")):
        session = regenerate_capture_visual_role(
            document.session,
            record_ref.record_id,
            _payload_value(action, "role"),
            dispatcher._paths,
        )
        return EditorActionResult(
            "success",
            dispatcher._rebuild(session, document),
            "Regenerated visual artifacts.",
        )
    if record_ref.record_type in {"capture", "measurement"}:
        return _regenerate_selected_item_artifact(dispatcher, document, action)
    if record_ref.record_type == "grid_dataset":
        session = generate_grid_dataset_overview_artifact(
            document.session,
            record_ref.record_id,
            dispatcher._paths.folder,
        )
        return EditorActionResult(
            "success",
            dispatcher._rebuild(session, document),
            "Regenerated grid overview.",
        )
    if record_ref.record_type == "report":
        return regenerate_report_artifact(dispatcher, document, action)
    if record_ref.record_type == "session_drawing":
        return _regenerate_session_drawing(
            dispatcher,
            document,
            action.item_id,
            record_ref.record_id,
        )
    return EditorActionResult(
        "unavailable",
        document,
        f"{item.label} does not have a refreshable drawing.",
    )


def _is_capture_visual_role(record_type: str, role: str) -> bool:
    return record_type == "capture" and role in {
        "site_image_labeled",
        "site_overview_image",
        "annotation_image",
        "visual_artifacts",
    }


def _regenerate_selected_item_artifact(
    dispatcher: _ArtifactRenderingDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    item = document.items_by_id[action.item_id]
    if item.record_ref is None:
        return EditorActionResult("unavailable", document, "No refreshable item is selected.")
    target = target_for_selected_artifact(document, item.record_ref, action)
    if target is None:
        return EditorActionResult(
            "unavailable",
            document,
            "The selected artifact does not belong to the selected item.",
        )
    render_result = _refresh_targets(dispatcher, document.session, (target,))
    return EditorActionResult(
        render_result.status,
        dispatcher._rebuild(render_result.session, document),
        render_result.message,
    )


def _regenerate_session_drawing(
    dispatcher: _ArtifactRenderingDispatcher,
    document: SessionDocument,
    item_id: str,
    drawing_id: str,
) -> EditorActionResult:
    cross_section = _cross_section_input_for(dispatcher, item_id, drawing_id)
    if cross_section is None:
        return EditorActionResult(
            "unavailable",
            document,
            "No cross-section render input is available for this drawing.",
        )
    render_result = _render_bridge_for_paths(dispatcher).refresh(
        document.session,
        RenderRefreshRequest(cross_sections=(cross_section,)),
    )
    return EditorActionResult(
        render_result.status,
        dispatcher._rebuild(render_result.session, document),
        render_result.message,
    )


def _refresh_targets(
    dispatcher: _ArtifactRenderingDispatcher,
    session: SessionRecord,
    targets: tuple[RenderTarget, ...],
) -> RenderRefreshResult:
    return _render_bridge_for_paths(dispatcher).refresh(
        session,
        RenderRefreshRequest(targets=targets),
    )


def _render_bridge_for_paths(dispatcher: _ArtifactRenderingDispatcher) -> SessionRenderBridge:
    if dispatcher._render_bridge is not None:
        return dispatcher._render_bridge
    if dispatcher._paths is None:
        raise RuntimeError("Session paths are required for rendering.")
    return SessionRenderBridge(dispatcher._paths, mode_registry=dispatcher._mode_registry)


def _cross_section_input_for(
    dispatcher: _ArtifactRenderingDispatcher,
    item_id: str,
    drawing_id: str,
) -> Optional[CrossSectionRenderInput]:
    inputs = dispatcher._cross_section_inputs
    return inputs.get(item_id) or inputs.get(drawing_id)
