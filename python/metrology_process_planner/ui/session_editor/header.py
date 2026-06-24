"""Header and status presenters for the unified session editor."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType
from metrology_process_planner.workflows.setup_guide_state import SetupGuideStateMachine
from metrology_process_planner.workflows.ui_state_machines import (
    RecipeContextStateMachine,
    SessionUIStateMachine,
)


def header_entries(document: SessionDocument) -> tuple[tuple[str, str], ...]:
    """Return session editor header fields for the modeless home surface."""

    selected = document.items_by_id[document.selection.selected_item_id]
    return (
        ("Session", document.session.name),
        ("Mode", document.session.mode.value),
        ("Output Folder", document.session.paths.artifact_root),
        ("Setup", SetupGuideStateMachine().evaluate(document.session).state.value),
        ("Capture", SessionUIStateMachine().evaluate(document.session).state),
        ("Selected", f"{selected.label} ({selected.status})"),
        ("Dirty", "Unsaved" if document.dirty_state.is_dirty else "Saved"),
        ("Warnings", str(len(document.warning_view_models))),
        ("Process Context", RecipeContextStateMachine().evaluate(document.session).state),
    )


def primary_actions(document: SessionDocument) -> tuple[EditorAction, ...]:
    """Return command-shaped primary actions for the editor header."""

    selected_id = document.selection.selected_item_id
    actions = [
        EditorAction(EditorActionType.SAVE_EDITS, "Save Edits", selected_id),
    ]
    if document.pending_capture_item_id:
        actions.append(
            EditorAction(
                EditorActionType.SELECT_ITEM,
                "Resume Capture",
                document.pending_capture_item_id,
            )
        )
    actions.extend(
        (
            EditorAction(EditorActionType.REOPEN_SETUP, "Reopen Setup", selected_id),
            *_process_actions(document, selected_id),
            EditorAction(EditorActionType.EXPORT_CSV, "Export CSV", selected_id),
            EditorAction(EditorActionType.BUILD_POWERPOINT, "Build Report", selected_id),
            EditorAction(EditorActionType.OPEN_OUTPUT_FOLDER, "Open Output Folder", selected_id),
            EditorAction(EditorActionType.EXIT_SESSION, "Close", selected_id),
        )
    )
    return tuple(actions)


def status_text(document: SessionDocument) -> str:
    """Return the bottom status strip text for the selected editor item."""

    selected = document.items_by_id[document.selection.selected_item_id]
    if document.warning_view_models:
        return f"{len(document.warning_view_models)} warning(s); selected {selected.label}"
    if document.pending_capture_item_id:
        return "Pending capture review is waiting in the editor."
    if document.dirty_state.is_dirty:
        return "Unsaved editor changes."
    return f"Ready; selected {selected.label}"


def _process_actions(document: SessionDocument, selected_id: str) -> tuple[EditorAction, ...]:
    state = RecipeContextStateMachine().evaluate(document.session).state
    if state == "none" and not _process_aware(document):
        return ()
    if state == "attached":
        return (
            EditorAction(
                EditorActionType.VALIDATE_PROCESS_CONTEXT,
                "Validate Process Context",
                selected_id,
            ),
        )
    return (EditorAction(EditorActionType.ATTACH_RECIPE, "Attach Recipe", selected_id),)


def _process_aware(document: SessionDocument) -> bool:
    mode = document.session.mode.value
    return bool(
        document.session.process_context.recipe_id
        or document.session.process_context.recipe_path
        or document.session.process_context.warning_ids
        or "process" in mode
        or mode in {"profilometry_planner", "ellipsometry_planner"}
    )
