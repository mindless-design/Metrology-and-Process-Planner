"""Command handlers for modeless setup-guide workflow actions."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    SessionRecord,
    SetupState,
)
from metrology_process_planner.domains.session.workflow import WorkflowState
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext


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
