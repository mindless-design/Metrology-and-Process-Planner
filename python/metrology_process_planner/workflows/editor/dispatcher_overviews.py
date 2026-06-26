"""Overview artifact editor dispatch handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.modes.mode_registry import built_in_mode_registry
from metrology_process_planner.domains.session import utc_now_iso
from metrology_process_planner.rendering.overview import (
    UserLabelRecord,
    default_overview_request,
    generate_overview_artifact,
    user_labels_from_session,
    with_user_label,
)
from metrology_process_planner.workflows.canvas_interaction_helpers import next_id
from metrology_process_planner.workflows.editor.dispatcher_results import EditorActionResult
from metrology_process_planner.workflows.editor.document import SessionDocument
from metrology_process_planner.workflows.editor.view_models import EditorAction

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.dispatcher import EditorActionDispatcher


def generate_session_overview_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Generate the default session overview artifact."""

    return generate_overview(dispatcher, document, "session_overview")


def generate_metrology_overview_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Generate the metrology overview artifact."""

    return generate_overview(dispatcher, document, "metrology_overview")


def generate_grid_overview_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    _action: EditorAction,
) -> EditorActionResult:
    """Generate the grid overview artifact."""

    return generate_overview(dispatcher, document, "grid_overview")


def regenerate_overview_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Regenerate an existing overview artifact by item role."""

    role = action.item_id.split(":", 1)[1] if ":" in action.item_id else "session_overview"
    return generate_overview(dispatcher, document, role)


def add_user_label_action(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    action: EditorAction,
) -> EditorActionResult:
    """Add a durable overview user label without opening a blocking dialog."""

    payload = dict(action.payload)
    labels = user_labels_from_session(document.session)
    label_id = next_id("user-label", (item.label_id for item in labels))
    now = utc_now_iso()
    label = UserLabelRecord(
        label_id,
        _label_geometry(payload),
        str(payload.get("title", "User Label")),
        notes=str(payload.get("notes", "")),
        created_at=now,
        modified_at=now,
    )
    updated = dispatcher._rebuild(with_user_label(document.session, label), document)
    return EditorActionResult("success", updated, "Added user overview label.")


def generate_overview(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    role: str,
) -> EditorActionResult:
    """Generate one overview artifact and rebuild the editor document."""

    unavailable = _unavailable_role(dispatcher, document, role)
    if unavailable is not None:
        return unavailable
    if dispatcher._paths is None:
        return EditorActionResult("unavailable", document, "No session folder is configured.")
    request = default_overview_request(document.session, role)
    session = generate_overview_artifact(document.session, dispatcher._paths.folder, request)
    updated = dispatcher._rebuild(session, document)
    return EditorActionResult(
        "success",
        updated,
        f"Generated {role.replace('_', ' ')}.",
        dispatcher._paths.folder / "artifacts" / "overviews" / f"{role}.svg",
    )


def _unavailable_role(
    dispatcher: EditorActionDispatcher,
    document: SessionDocument,
    role: str,
) -> EditorActionResult | None:
    registry = dispatcher._mode_registry or built_in_mode_registry()
    mode = registry.definition(document.session.mode.value)
    if role == "metrology_overview" and mode.family != "metrology":
        return _unavailable(document, "Metrology overview is not available for this mode.")
    if role == "grid_overview" and not mode.capabilities.supports_grid_datasets:
        return _unavailable(document, "Grid overview is not available for this mode.")
    return None


def _unavailable(document: SessionDocument, message: str) -> EditorActionResult:
    return EditorActionResult("unavailable", document, message)


def _label_geometry(payload: dict[str, str]) -> dict[str, object]:
    bounds = Box(
        _float(payload, "left", 0.0),
        _float(payload, "bottom", 0.0),
        _float(payload, "right", 10.0),
        _float(payload, "top", 10.0),
    )
    return {"kind": "box", "bounds": bounds.to_dict()}


def _float(payload: dict[str, str], key: str, default: float) -> float:
    try:
        return float(payload.get(key, default))
    except ValueError:
        return default
