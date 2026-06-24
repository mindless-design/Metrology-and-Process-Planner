"""Command handlers for modeless setup-guide workflow actions."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.command_types import CommandId
from metrology_process_planner.app.commands import CommandRegistry
from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    SessionRecord,
    SetupItemRecord,
    SetupState,
)
from metrology_process_planner.domains.session.workflow import WorkflowState
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext
from metrology_process_planner.workflows.process_context import validate_process_context


class SetupGuideCommandService:
    """Apply setup guide commands through shared workflow primitives."""

    def __init__(
        self,
        setup_guide: SetupGuideController,
        canvas_engine: CanvasInteractionEngine,
    ) -> None:
        self._setup_guide = setup_guide
        self._canvas_engine = canvas_engine
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

        setup = replace(self._session().setup, is_capture_ready=True)
        self.context = self._canvas_engine.disarm_capture(self.context)
        self._set_session(replace(self._session(), setup=setup, workflow=WorkflowState()))

    def skip_optional_setup_stage(self) -> None:
        """Mark the active optional explicit setup stage as skipped."""

        session = self._session()
        skipped = _skip_first_optional_item(session.setup.items)
        self._set_session(replace(session, setup=replace(session.setup, items=skipped)))

    def validate_recipe_context(self) -> None:
        """Validate recipe/process setup context and persist warnings."""

        result = validate_process_context(self._session())
        self._set_session(result.session)

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
        (CommandId.START_ALIGNMENT_CAPTURE, setup_commands.start_alignment_capture),
        (CommandId.START_SEM_ALIGNMENT_CAPTURE, setup_commands.start_sem_alignment_capture),
        (CommandId.SKIP_OPTIONAL_SETUP_STAGE, setup_commands.skip_optional_setup_stage),
        (CommandId.VALIDATE_RECIPE_CONTEXT, setup_commands.validate_recipe_context),
        (CommandId.MARK_SETUP_COMPLETE, setup_commands.mark_setup_complete),
    ):
        command_registry.register(command_id, handler)


def _skip_first_optional_item(items: tuple[SetupItemRecord, ...]) -> tuple[SetupItemRecord, ...]:
    updated: list[SetupItemRecord] = []
    skipped = False
    for item in items:
        if not skipped and not _is_required(item) and item.status != "complete":
            updated.append(replace(item, status="skipped"))
            skipped = True
        else:
            updated.append(item)
    return tuple(updated)


def _is_required(item: SetupItemRecord) -> bool:
    return bool(dict(item.metadata or {}).get("required", True))
