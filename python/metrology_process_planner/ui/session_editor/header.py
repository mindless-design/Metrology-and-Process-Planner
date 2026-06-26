"""Header and status presenters for the unified session editor."""

from __future__ import annotations

from metrology_process_planner.domains.session import ModeRegistry, session_mode_value
from metrology_process_planner.domains.warnings.warning_visibility import session_is_process_aware
from metrology_process_planner.ui.session_editor.header_status import status_text
from metrology_process_planner.workflows.capture_readiness import capture_blocked_by_setup_message
from metrology_process_planner.workflows.editor.adapters import SessionModeAdapter
from metrology_process_planner.workflows.editor.builder_basics import (
    mode_is_process_aware,
    mode_uses_setup,
)
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType
from metrology_process_planner.workflows.measurement_completion import measurement_completion_prompt
from metrology_process_planner.workflows.setup_guide_state import SetupGuideStateMachine
from metrology_process_planner.workflows.ui_state_machines import (
    RecipeContextStateMachine,
    SessionUIStateMachine,
)

__all__ = ["header_entries", "primary_actions", "status_text"]


def header_entries(
    document: SessionDocument,
    adapter: SessionModeAdapter | None = None,
) -> tuple[tuple[str, str], ...]:
    """Return session editor header fields for the modeless home surface."""

    selected = document.items_by_id[document.selection.selected_item_id]
    entries = [
        ("Session", document.session.name),
        ("Mode", document.session.mode.value),
        ("Output Folder", document.session.paths.artifact_root),
        ("Capture", SessionUIStateMachine().evaluate(document.session).state),
        ("Selected", f"{selected.label} ({selected.status})"),
        ("Dirty", "Unsaved" if document.dirty_state.is_dirty else "Saved"),
        ("Warnings", str(len(document.warning_view_models))),
    ]
    if _mode_uses_setup(document, adapter):
        entries.insert(
            3,
            ("Setup", _setup_state(document, adapter)),
        )
    registry = _mode_registry(adapter)
    if _process_aware(document, adapter):
        entries.append(
            (
                "Process Context",
                RecipeContextStateMachine(registry).evaluate(document.session).state,
            )
        )
    return tuple(entries)


def primary_actions(
    document: SessionDocument,
    adapter: SessionModeAdapter | None = None,
) -> tuple[EditorAction, ...]:
    """Return command-shaped primary actions for the editor header."""

    prompt = measurement_completion_prompt(document.session)
    if prompt is not None:
        return _completion_prompt_actions(document, prompt.choices)

    selected_id = document.selection.selected_item_id
    actions = [
        EditorAction(EditorActionType.SAVE_EDITS, "Save Edits", selected_id),
    ]
    actions.extend(_capture_actions(document, selected_id, adapter))
    if _mode_uses_setup(document, adapter):
        actions.append(EditorAction(EditorActionType.REOPEN_SETUP, "Reopen Setup", selected_id))
    actions.extend(
        (*_process_actions(document, selected_id, adapter), *_report_actions(selected_id))
    )
    return tuple(actions)


def _capture_actions(
    document: SessionDocument,
    selected_id: str,
    adapter: SessionModeAdapter | None,
) -> tuple[EditorAction, ...]:
    actions: list[EditorAction] = []
    if not _process_aware(document, adapter) and not document.session.workflow.active:
        blocked_reason = capture_blocked_by_setup_message(
            document.session,
            _mode_registry(adapter),
        )
        actions.append(
            EditorAction(
                EditorActionType.ADD_CAPTURE,
                _add_capture_label(document),
                selected_id,
                enabled=not blocked_reason,
                disabled_reason=blocked_reason,
            )
        )
    if document.session.workflow.active:
        actions.append(
            EditorAction(
                EditorActionType.CANCEL_CAPTURE,
                _cancel_capture_label(document),
                selected_id,
            )
        )
    if document.pending_capture_item_id:
        actions.append(
            EditorAction(
                EditorActionType.SELECT_ITEM,
                "Resume Capture",
                document.pending_capture_item_id,
            )
        )
    return tuple(actions)


def _report_actions(selected_id: str) -> tuple[EditorAction, ...]:
    return (
        EditorAction(EditorActionType.EXPORT_CSV, "Export CSV", selected_id),
        EditorAction(
            EditorActionType.BUILD_POWERPOINT,
            "Build Report",
            selected_id,
        ),
        EditorAction(EditorActionType.OPEN_OUTPUT_FOLDER, "Open Output Folder", selected_id),
        EditorAction(EditorActionType.EXIT_SESSION, "Close", selected_id),
    )


def _process_actions(
    document: SessionDocument,
    selected_id: str,
    adapter: SessionModeAdapter | None,
) -> tuple[EditorAction, ...]:
    if not _process_aware(document, adapter):
        return ()
    state = RecipeContextStateMachine(_mode_registry(adapter)).evaluate(document.session).state
    if state == "attached":
        return (
            EditorAction(
                EditorActionType.VALIDATE_PROCESS_CONTEXT,
                "Validate Process Context",
                selected_id,
            ),
        )
    return (EditorAction(EditorActionType.ATTACH_RECIPE, "Attach Recipe", selected_id),)


def _process_aware(
    document: SessionDocument,
    adapter: SessionModeAdapter | None = None,
) -> bool:
    registry = _mode_registry(adapter)
    if registry is not None:
        return mode_is_process_aware(document.session, registry)
    return session_is_process_aware(document.session)


def _mode_uses_setup(
    document: SessionDocument,
    adapter: SessionModeAdapter | None = None,
) -> bool:
    return mode_uses_setup(document.session, _mode_registry(adapter))


def _setup_state(
    document: SessionDocument,
    adapter: SessionModeAdapter | None = None,
) -> str:
    registry = _mode_registry(adapter)
    mode = registry.definition(document.session.mode.value) if registry is not None else None
    return SetupGuideStateMachine().evaluate(document.session, mode).state.value


def _mode_registry(adapter: SessionModeAdapter | None) -> ModeRegistry | None:
    return getattr(adapter, "_mode_registry", None)


def _completion_prompt_actions(
    document: SessionDocument,
    choices: tuple[tuple[str, str], ...],
) -> tuple[EditorAction, ...]:
    action_types = {
        "take_another_measurement": EditorActionType.TAKE_ANOTHER_MEASUREMENT,
        "return_to_editor": EditorActionType.RETURN_TO_EDITOR,
        "done": EditorActionType.DONE,
    }
    selected_id = document.selection.selected_item_id
    return tuple(
        EditorAction(action_types[choice_id], label, selected_id)
        for choice_id, label in choices
        if choice_id in action_types
    )


def _add_capture_label(document: SessionDocument) -> str:
    if session_mode_value(document.session.mode) == "fast_batch_capture":
        return "Start Batch Capture"
    return "Add Capture"


def _cancel_capture_label(document: SessionDocument) -> str:
    if session_mode_value(document.session.mode) == "fast_batch_capture":
        return "Exit Batch Capture"
    return "Cancel Capture"
