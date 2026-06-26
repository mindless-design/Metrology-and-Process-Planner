"""Command handlers for modeless capture arming and cancellation."""

from __future__ import annotations

from dataclasses import replace
from typing import Optional, Protocol

from metrology_process_planner.app.command_types import CommandBlockedError, CommandId
from metrology_process_planner.app.commands import CommandRegistry
from metrology_process_planner.app.recipe_session_attachment import (
    active_session_from_editor,
    refresh_editor_session,
)
from metrology_process_planner.app.session_editor import SessionEditorController
from metrology_process_planner.app.setup_guide import SetupGuideController
from metrology_process_planner.domains.session import (
    CanvasObjectType,
    CanvasVisualFlag,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.domains.session.workflow import WorkflowState
from metrology_process_planner.workflows import CanvasInteractionEngine, InteractionContext
from metrology_process_planner.workflows.capture_readiness import (
    capture_blocked_by_setup_message,
)


class SessionProvider(Protocol):
    """Callable that returns the session currently controlled by modeless UI."""

    def __call__(self) -> Optional[SessionRecord]:
        """Return the active session or None."""


class SessionUpdater(Protocol):
    """Callable that publishes an updated active session."""

    def __call__(self, session: SessionRecord) -> None:
        """Publish an updated session."""


class CaptureCommandService:
    """Apply generic capture commands through shared canvas primitives."""

    def __init__(
        self,
        canvas_engine: CanvasInteractionEngine,
        session_provider: SessionProvider,
        session_updater: SessionUpdater,
        mode_registry: ModeRegistry | None = None,
    ) -> None:
        self._canvas_engine = canvas_engine
        self._session_provider = session_provider
        self._session_updater = session_updater
        self._mode_registry = mode_registry
        self.context = InteractionContext()

    def start_capture(self) -> None:
        """Arm the default generic box capture primitive."""

        self.start_box_capture()

    def start_box_capture(self) -> None:
        """Arm generic Shift-drag site box capture."""

        session = self._session()
        setup_block = capture_blocked_by_setup_message(session, self._mode_registry)
        if setup_block:
            raise CommandBlockedError(
                setup_block,
                "Complete required setup cards before starting site capture.",
            )
        self.context = self._canvas_engine.arm_box_capture(self.context)
        self._set_session(_armed_session(session, "box_capture", CanvasObjectType.SITE_BOX))

    def start_line_capture(self) -> None:
        """Arm generic Shift-drag line capture."""

        session = self._session()
        parent_id = _selected_canvas_parent(session)
        self.context = self._canvas_engine.arm_line_capture(self.context, parent_id)
        self._set_session(_armed_session(session, "line_capture", CanvasObjectType.MEASUREMENT))

    def start_point_capture(self) -> None:
        """Arm generic Shift-click point capture."""

        session = self._session()
        parent_id = _selected_canvas_parent(session)
        self.context = self._canvas_engine.arm_point_capture(self.context, parent_id)
        self._set_session(_armed_session(session, "point_capture", CanvasObjectType.POINT))

    def cancel_capture(self) -> None:
        """Cancel active capture arming and clear transient preview state."""

        session = self._session()
        result = self._canvas_engine.exit_capture(session, self.context)
        self.context = result.context
        self._set_session(replace(result.session, workflow=WorkflowState()))

    def _session(self) -> SessionRecord:
        session = self._session_provider()
        if session is None:
            raise RuntimeError("No active session is loaded.")
        return session

    def _set_session(self, session: SessionRecord) -> None:
        self._session_updater(session)


def register_capture_command_handlers(
    command_registry: CommandRegistry,
    capture_commands: CaptureCommandService,
) -> None:
    """Register modeless capture command handlers."""

    for command_id, handler in (
        (CommandId.START_CAPTURE, capture_commands.start_capture),
        (CommandId.START_BOX_CAPTURE, capture_commands.start_box_capture),
        (CommandId.START_LINE_CAPTURE, capture_commands.start_line_capture),
        (CommandId.START_POINT_CAPTURE, capture_commands.start_point_capture),
        (CommandId.CANCEL_CAPTURE, capture_commands.cancel_capture),
    ):
        command_registry.register(command_id, handler)


def active_capture_session(
    session_editor: SessionEditorController,
    setup_guide: SetupGuideController,
) -> SessionRecord | None:
    """Return the active editor session, falling back to the setup guide."""

    session = active_session_from_editor(session_editor)
    if session is not None:
        return session
    return setup_guide.active_session


def refresh_capture_session(
    session_editor: SessionEditorController,
    setup_guide: SetupGuideController,
    session: SessionRecord,
) -> None:
    """Refresh all modeless surfaces currently looking at the session."""

    if session_editor.current_document is not None:
        refresh_editor_session(session_editor, session)
    if setup_guide.active_session is not None and setup_guide.active_session.id == session.id:
        setup_guide.set_active_session(session)


def _armed_session(
    session: SessionRecord,
    stage: str,
    primitive: CanvasObjectType,
) -> SessionRecord:
    workflow = replace(
        session.workflow,
        active=True,
        stage=stage,
        active_mode=session.mode.value,
        active_primitive=primitive.value,
        pending_item_ref=f"capture:{stage}",
    )
    return replace(session, workflow=workflow)


def _selected_canvas_parent(session: SessionRecord) -> str | None:
    for canvas_object in session.canvas_objects:
        if CanvasVisualFlag.SELECTED in canvas_object.visual_state:
            return canvas_object.id
    return None
