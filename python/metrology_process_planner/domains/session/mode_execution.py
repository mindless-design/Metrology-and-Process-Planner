"""Execution planning contracts for declarative workflow modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from metrology_process_planner.domains.session.mode_registry import ModeDefinition


@dataclass(frozen=True)
class ModeExecutionContext:
    """Runtime context used to map a mode onto shared workflow services."""

    mode_definition: ModeDefinition
    session_document: Any | None = None
    source_layout_context: Any | None = None
    active_view_binding: Any | None = None
    command_router: Any | None = None
    services: Any | None = None
    workflow_state: Any | None = None


class ModeWorkflowPlanner:
    """Map declarative mode policies onto shared workflow requests."""

    def compound_capture_request(
        self,
        definition: ModeDefinition,
    ) -> Any:
        """Return a shared compound capture request for a compound mode."""

        from metrology_process_planner.workflows.compound_capture_models import (
            CompoundCaptureRequest,
        )

        capture = definition.capture
        if capture.primitive_type not in {"site_then_line", "site_then_point"}:
            raise ValueError(f"Mode {definition.mode_id} is not a compound capture mode.")
        return CompoundCaptureRequest(
            definition.mode_id,
            capture.primitive_type,
            capture.site_role,
            capture.inner_feature_role,
            capture.inner_feature_kind,
            capture.inner_feature_label,
            capture.child_canvas_object_type,
            definition.process.recipe_policy,
            definition.process.solver_operation,
            definition.process.render_profile,
            definition.artifacts.annotation_role_on_capture_save(),
            definition.artifacts.process_roles_on_capture_save(),
            capture.saved_capture_type,
            capture.extension_key,
            capture.feature_id_field,
            capture.process_output_key,
            capture.repeat_label_template,
        )

    def metadata_field_ids(self, definition: ModeDefinition) -> tuple[str, ...]:
        """Return metadata field ids used by review/editor forms."""

        return definition.metadata.field_ids()

    def capture_artifact_roles(self, definition: ModeDefinition) -> tuple[str, ...]:
        """Return capture-save artifact roles requested by a mode."""

        return definition.artifacts.roles_on_capture_save()

    def editor_action_ids(self, definition: ModeDefinition) -> tuple[str, ...]:
        """Return editor action ids requested by a mode."""

        return definition.editor.actions
