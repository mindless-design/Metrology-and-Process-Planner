"""Editor dispatch helpers for capture visual polish regeneration."""

from __future__ import annotations

from typing import Protocol

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
    generate_annotation_artifact,
    generate_labeled_site_artifact,
    generate_site_overview_artifact,
    generate_visual_artifacts_for_capture,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument

VISUAL_CAPTURE_ROLES = {
    "site_image_labeled",
    "site_overview_image",
    "annotation_image",
    "visual_artifacts",
}


class _CaptureVisualDispatcher(Protocol):
    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after workflow state changes."""


def regenerate_capture_visual_action(
    dispatcher: _CaptureVisualDispatcher,
    document: SessionDocument,
    capture_id: str,
    role: str,
    paths: SessionPaths,
) -> EditorActionResult:
    """Regenerate selected capture visual artifacts and rebuild the editor document."""

    session = regenerate_capture_visual_role(document.session, capture_id, role, paths)
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Regenerated visual artifacts.",
    )


def regenerate_capture_visual_role(
    session: SessionRecord,
    capture_id: str,
    role: str,
    paths: SessionPaths,
) -> SessionRecord:
    """Return a session with one or all capture visual artifacts regenerated."""

    capture = next((item for item in session.captures if item.id == capture_id), None)
    if capture is None:
        return session
    if role == "visual_artifacts":
        return generate_visual_artifacts_for_capture(session, capture_id, paths)
    if role == "site_image_labeled":
        return generate_labeled_site_artifact(session, capture, paths)
    if role == "site_overview_image":
        return generate_site_overview_artifact(session, capture, paths)
    return generate_annotation_artifact(session, capture, paths)
