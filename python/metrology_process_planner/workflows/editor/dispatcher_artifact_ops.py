"""Artifact repair operations used by editor regeneration dispatch."""

from __future__ import annotations

from typing import Optional, Protocol

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.artifacts.visual_capture_generator import (
    generate_annotation_artifact,
    generate_labeled_site_artifact,
    generate_site_overview_artifact,
    generate_visual_artifacts_for_capture,
)
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.dispatcher_support import _payload_value
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction


class _ArtifactOpsDispatcher(Protocol):
    """Dispatcher fields needed by repair-oriented artifact actions."""

    _paths: Optional[SessionPaths]
    _mode_registry: ModeRegistry | None

    def _rebuild(self, session: SessionRecord, document: SessionDocument) -> SessionDocument:
        """Rebuild a document after workflow state changes."""


def regenerate_setup_artifact(
    dispatcher: _ArtifactOpsDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Regenerate a selected setup artifact through the repair service."""

    artifact_id = _payload_value(action, "artifact_id")
    if not artifact_id:
        return EditorActionResult(
            "unavailable",
            document,
            "Setup regeneration requires a selected setup artifact.",
        )
    artifact = (document.session.artifacts or {}).get(artifact_id)
    if artifact is None or artifact.owner.owner_type != "setup":
        return EditorActionResult("unavailable", document, "Setup artifact no longer exists.")
    assert dispatcher._paths is not None
    session = ArtifactRepairService().repair_artifact(
        document.session,
        artifact_id,
        dispatcher._paths,
    )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Regenerated setup artifact.",
    )


def regenerate_report_artifact(
    dispatcher: _ArtifactOpsDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Regenerate a selected report artifact through the repair service."""

    artifact_id = _payload_value(action, "artifact_id")
    if not artifact_id:
        return EditorActionResult(
            "unavailable",
            document,
            "Report regeneration requires a selected report artifact.",
        )
    if artifact_id not in (document.session.artifacts or {}):
        return EditorActionResult("unavailable", document, "Report artifact no longer exists.")
    assert dispatcher._paths is not None
    session = ArtifactRepairService().repair_artifact(
        document.session,
        artifact_id,
        dispatcher._paths,
    )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        "Regenerated report artifact.",
    )


def relink_artifact(
    dispatcher: _ArtifactOpsDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Relink a payload-selected artifact to a replacement relative path."""

    artifact_id = _payload_value(action, "artifact_id")
    relative_path = _payload_value(action, "relative_path")
    if not artifact_id or not relative_path:
        return EditorActionResult(
            "unavailable",
            document,
            "Relink artifact requires a selected replacement path.",
        )
    artifact = (document.session.artifacts or {}).get(artifact_id)
    if artifact is None or not artifact_visible_for_session(
        document.session,
        artifact,
        dispatcher._mode_registry,
    ):
        return EditorActionResult(
            "unavailable",
            document,
            "Relink artifact is not available for this recipe-free mode.",
        )
    session = ArtifactRepairService().relink_artifact(
        document.session,
        artifact_id,
        relative_path,
        dispatcher._mode_registry,
    )
    return EditorActionResult(
        "success",
        dispatcher._rebuild(session, document),
        f"Artifact relinked: {artifact_id}",
    )


def regenerate_capture_visual_role(
    session: SessionRecord,
    capture_id: str,
    role: str,
    paths: SessionPaths,
) -> SessionRecord:
    """Regenerate a capture-scoped visual artifact role."""

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
