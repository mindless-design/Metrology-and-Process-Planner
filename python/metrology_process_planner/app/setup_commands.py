"""Command handlers for modeless setup-guide workflow actions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from metrology_process_planner.app.command_types import CommandBlockedError, CommandId
from metrology_process_planner.app.commands import CommandRegistry
from metrology_process_planner.app.recipe_path_adapter import (
    RecipePathAdapter,
    UnavailableRecipePathAdapter,
)
from metrology_process_planner.app.setup_command_stages import (
    active_optional_skip_item,
    ensure_active_stage_is_optional,
    incomplete_required_setup_labels,
    skip_optional_item,
)
from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.app.setup_recipe_attachment import attach_selected_recipe
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    ModeRegistry,
    SessionRecord,
    SetupState,
    built_in_mode_registry,
)
from metrology_process_planner.domains.session.workflow import WorkflowState
from metrology_process_planner.ui.shell import CommandRouteResult
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware
from metrology_process_planner.workflows.process_context import validate_process_context


class SetupGuideCommandService:
    """Apply setup guide commands through shared workflow primitives."""

    def __init__(
        self,
        setup_guide: SetupGuideController,
        canvas_engine: CanvasInteractionEngine,
        session_updater: Callable[[SessionRecord], None] | None = None,
        recipe_path_adapter: RecipePathAdapter | None = None,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._setup_guide = setup_guide
        self._canvas_engine = canvas_engine
        self._session_updater = session_updater
        self._recipe_path_adapter = recipe_path_adapter or UnavailableRecipePathAdapter()
        self._mode_registry = mode_registry or built_in_mode_registry()
        self.context = InteractionContext()
    def use_global_coordinates(self) -> None:
        """Mark setup as using the source layout's global coordinates."""
        self._update_setup(replace(self._session().setup, coordinate_mode="global"))

    def use_origin_coordinates(self) -> None:
        """Mark setup as requiring a user-defined origin."""
        self._update_setup(replace(self._session().setup, coordinate_mode="origin"))

    def start_origin_point_capture(self) -> None:
        """Arm the shared point capture primitive for setup origin capture."""

        self.context = self._canvas_engine.arm_point_capture(self.context)
        self._arm_workflow("origin_point_capture", CanvasObjectType.POINT)

    def start_origin_reference_capture(self) -> None:
        """Arm the shared box capture primitive for origin reference capture."""

        self._arm_box("origin_reference_box_capture")

    def start_alignment_capture(self) -> None:
        """Arm the shared box capture primitive for optical alignment capture."""

        self._arm_box("alignment_box_capture")

    def start_sem_alignment_capture(self) -> None:
        """Arm the shared box capture primitive for SEM alignment capture."""

        self._arm_box("sem_alignment_box_capture")

    def mark_setup_complete(self) -> None:
        """Mark setup ready and clear any active setup capture arming."""

        incomplete = incomplete_required_setup_labels(self._session(), self._mode_registry)
        if incomplete:
            raise CommandBlockedError(
                "Setup is blocked by incomplete required stage(s): " + ", ".join(incomplete),
                "Complete required setup cards before marking the session ready.",
            )
        setup = replace(self._session().setup, is_capture_ready=True)
        self.context = self._canvas_engine.disarm_capture(self.context)
        self._set_session(replace(self._session(), setup=setup, workflow=WorkflowState()))

    def skip_optional_setup_stage(self) -> None:
        """Mark the active optional explicit setup stage as skipped."""

        session = self._session()
        active = ensure_active_stage_is_optional(session, self._mode_registry)
        skipped = skip_optional_item(session.setup.items, active)
        if skipped == session.setup.items:
            skipped = session.setup.items + (active_optional_skip_item(active),)
        self._set_session(replace(session, setup=replace(session.setup, items=skipped)))

    def validate_recipe_context(self) -> None:
        """Validate recipe/process setup context and persist warnings."""

        if not mode_is_process_aware(self._session(), self._mode_registry):
            raise CommandBlockedError(
                "Recipe validation is not available for this recipe-free mode.",
                "Continue setup without attaching a process recipe.",
            )
        result = validate_process_context(self._session())
        self._set_session(result.session)

    def attach_recipe(self) -> CommandRouteResult:
        """Attach a picker-selected recipe to the active setup session."""

        session, result = attach_selected_recipe(
            self._session(),
            self._recipe_path_adapter,
            self._mode_registry,
        )
        self._set_session(session)
        return result

    def _arm_box(self, stage: str) -> None:
        self.context = self._canvas_engine.arm_box_capture(self.context)
        self._arm_workflow(stage, CanvasObjectType.SITE_BOX)

    def _arm_workflow(self, stage: str, primitive: CanvasObjectType) -> None:
        session = self._session()
        workflow = replace(
            session.workflow,
            active=True,
            stage=stage,
            active_mode=session.mode.value,
            active_primitive=primitive.value,
            pending_item_ref=f"setup:{stage}",
        )
        self._set_session(replace(session, workflow=workflow))

    def _update_setup(self, setup: SetupState) -> None:
        self._set_session(replace(self._session(), setup=setup))

    def _session(self) -> SessionRecord:
        session = self._setup_guide.active_session
        if session is None:
            raise RuntimeError("No active session is loaded.")
        return session

    def _set_session(self, session: SessionRecord) -> None:
        self._setup_guide.set_active_session(session)
        if self._session_updater is not None:
            self._session_updater(session)


def register_setup_command_handlers(
    command_registry: CommandRegistry,
    setup_commands: SetupGuideCommandService,
) -> None:
    """Register modeless setup-guide command handlers."""

    for command_id, handler in (
        (CommandId.USE_GLOBAL_COORDINATES, setup_commands.use_global_coordinates),
        (CommandId.USE_ORIGIN_COORDINATES, setup_commands.use_origin_coordinates),
        (CommandId.START_ORIGIN_POINT_CAPTURE, setup_commands.start_origin_point_capture),
        (CommandId.START_ORIGIN_REFERENCE_CAPTURE, setup_commands.start_origin_reference_capture),
        (CommandId.START_OPTICAL_ALIGNMENT_CAPTURE, setup_commands.start_alignment_capture),
        (CommandId.START_ALIGNMENT_CAPTURE, setup_commands.start_alignment_capture),
        (CommandId.START_SEM_ALIGNMENT_CAPTURE, setup_commands.start_sem_alignment_capture),
        (CommandId.SKIP_OPTIONAL_SETUP_STAGE, setup_commands.skip_optional_setup_stage),
        (CommandId.ATTACH_RECIPE, setup_commands.attach_recipe),
        (CommandId.VALIDATE_RECIPE_CONTEXT, setup_commands.validate_recipe_context),
        (CommandId.MARK_SETUP_COMPLETE, setup_commands.mark_setup_complete),
    ):
        command_registry.register(command_id, handler)
