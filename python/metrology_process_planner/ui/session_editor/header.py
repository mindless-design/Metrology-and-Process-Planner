"""Header and status presenters for the unified session editor."""

from __future__ import annotations

from metrology_process_planner.workflows.editor.document import SessionDocument
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
