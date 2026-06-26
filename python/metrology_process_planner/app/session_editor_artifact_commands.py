"""Session editor command handlers for artifact lifecycle actions."""

from __future__ import annotations

from metrology_process_planner.app.commands import CommandId, CommandRegistry
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.session_editor_artifact_ops import (
    export_artifact_manifest_command,
    rebuilt_document,
    repair_all_command,
)
from metrology_process_planner.app.session_editor_command_dispatch import (
    dispatch_selected_editor_action,
)
from metrology_process_planner.app.session_editor_command_results import no_document
from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows.artifacts import ArtifactRepairService
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.view_models import EditorAction


class SessionEditorArtifactCommandService:
    """Translate artifact app commands into scanner and repair service calls."""

    def __init__(
        self,
        controller: SessionEditorController,
        repair_service: ArtifactRepairService | None = None,
    ) -> None:
        self._controller = controller
        self._repair_service = repair_service or ArtifactRepairService()

    def scan_artifacts(self) -> CommandRouteResult:
        """Scan artifacts through the lifecycle service and refresh the editor."""

        document = self._controller.current_document
        paths = self._controller.current_paths
        if document is None:
            return no_document(CommandId.SCAN_ARTIFACTS, "scanning artifacts")
        if paths is None:
            return _unavailable(CommandId.SCAN_ARTIFACTS, "No session folder is available.")
        session, result = self._repair_service.scan_session(
            document.session,
            paths,
            self._controller.mode_registry,
        )
        self._controller.replace_current_document(
            SessionDocumentBuilder(mode_registry=self._controller.mode_registry).build(session)
        )
        return CommandRouteResult(
            CommandId.SCAN_ARTIFACTS,
            "success",
            f"Scanned {result.artifact_count} artifacts; {result.missing_count} missing.",
        )

    def regenerate_missing_artifacts(self) -> CommandRouteResult:
        """Repair all missing artifacts with currently available generators."""

        return self._repair_all(CommandId.REGENERATE_MISSING_ARTIFACTS, missing=True)

    def regenerate_stale_artifacts(self) -> CommandRouteResult:
        """Repair all stale artifacts with currently available generators."""

        return self._repair_all(CommandId.REGENERATE_STALE_ARTIFACTS, missing=False)

    def regenerate_artifact(self) -> CommandRouteResult:
        """Regenerate one payload-selected artifact through the repair service."""

        action = self._controller.routed_action
        artifact_id = _payload_value(action, "artifact_id")
        if not artifact_id:
            return self._legacy_regenerate_artifact()
        document = self._controller.current_document
        paths = self._controller.current_paths
        if document is None:
            return no_document(CommandId.REGENERATE_ARTIFACT, "regenerating artifact")
        if paths is None:
            return _unavailable(CommandId.REGENERATE_ARTIFACT, "No session folder is available.")
        session = self._repair_service.repair_artifact(
            document.session,
            artifact_id,
            paths,
            self._controller.mode_registry,
        )
        self._controller.replace_current_document(
            rebuilt_document(session, document, self._controller.mode_registry)
        )
        return CommandRouteResult(
            CommandId.REGENERATE_ARTIFACT,
            "success",
            f"Artifact repair processed: {artifact_id}",
        )

    def relink_artifact(self) -> CommandRouteResult:
        """Relink a payload-selected artifact to a replacement relative path."""

        action = self._controller.routed_action
        artifact_id = _payload_value(action, "artifact_id")
        relative_path = _payload_value(action, "relative_path")
        if not artifact_id or not relative_path:
            return _unavailable(
                CommandId.RELINK_ARTIFACT,
                "Relink artifact requires a selected replacement path.",
            )
        document = self._controller.current_document
        if document is None:
            return no_document(CommandId.RELINK_ARTIFACT, "relinking artifact")
        artifact = (document.session.artifacts or {}).get(artifact_id)
        if artifact is None or not artifact_visible_for_session(
            document.session,
            artifact,
            self._controller.mode_registry,
        ):
            return _unavailable(
                CommandId.RELINK_ARTIFACT,
                "Relink artifact is not available for this recipe-free mode.",
            )
        session = self._repair_service.relink_artifact(
            document.session,
            artifact_id,
            relative_path,
            self._controller.mode_registry,
        )
        self._controller.replace_current_document(
            rebuilt_document(session, document, self._controller.mode_registry)
        )
        return CommandRouteResult(
            CommandId.RELINK_ARTIFACT,
            "success",
            f"Artifact relinked: {artifact_id}",
        )

    def export_artifact_manifest(self) -> CommandRouteResult:
        """Export the current canonical artifact registry as JSON."""

        return export_artifact_manifest_command(
            self._controller.current_document,
            self._controller.current_paths,
            self._controller.mode_registry,
        )

    def _repair_all(self, command_id: CommandId, missing: bool) -> CommandRouteResult:
        return repair_all_command(
            command_id,
            self._controller.current_document,
            self._controller.current_paths,
            self._controller.mode_registry,
            self._repair_service,
            missing,
            self._controller.replace_current_document,
        )

    def _legacy_regenerate_artifact(self) -> CommandRouteResult:
        from metrology_process_planner.workflows.editor.view_models import EditorActionType

        return dispatch_selected_editor_action(
            self._controller,
            CommandId.REGENERATE_ARTIFACT,
            EditorActionType.REGENERATE_ARTIFACT,
        )


def register_artifact_command_handlers(
    registry: CommandRegistry,
    controller: SessionEditorController,
    repair_service: ArtifactRepairService | None = None,
) -> None:
    """Register session-editor-owned artifact lifecycle handlers."""

    service = SessionEditorArtifactCommandService(controller, repair_service)
    registry.register(CommandId.REGENERATE_ARTIFACT, service.regenerate_artifact)
    registry.register(CommandId.SCAN_ARTIFACTS, service.scan_artifacts)
    registry.register(CommandId.REGENERATE_MISSING_ARTIFACTS, service.regenerate_missing_artifacts)
    registry.register(CommandId.REGENERATE_STALE_ARTIFACTS, service.regenerate_stale_artifacts)
    registry.register(CommandId.RELINK_ARTIFACT, service.relink_artifact)
    registry.register(CommandId.EXPORT_ARTIFACT_MANIFEST, service.export_artifact_manifest)


def _unavailable(command_id: CommandId, message: str) -> CommandRouteResult:
    return CommandRouteResult(command_id, "unavailable", message)


def _payload_value(action: EditorAction | None, key: str) -> str:
    if action is None:
        return ""
    return str(dict(action.payload).get(key, ""))


