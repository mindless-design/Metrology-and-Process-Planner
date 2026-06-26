"""Dashboard action builders for the default editor adapter."""

from __future__ import annotations

from metrology_process_planner.domains.session import (
    CaptureRecord,
    ModeRegistry,
    SessionRecord,
    built_in_mode_registry,
    session_mode_value,
)
from metrology_process_planner.workflows.editor.adapter_dashboard_readiness import (
    visible_dashboard_artifacts,
)
from metrology_process_planner.workflows.editor.adapter_process import (
    dashboard_process_context_actions,
)
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType


def dashboard_actions(
    session: SessionRecord,
    item: SessionItem,
    mode_registry: ModeRegistry | None = None,
) -> tuple[EditorAction, ...]:
    """Return dashboard actions from mode policy."""

    mode = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    actions = list(
        artifact_dashboard_actions(
            item,
            session,
            mode.family,
            mode.capabilities.supports_grid_datasets,
            mode_registry,
        )
    )
    if _mode_is_process_aware(session, mode_registry):
        actions.extend(dashboard_process_context_actions(item.item_id))
    return tuple(actions)


def artifact_dashboard_actions(
    item: SessionItem,
    session: SessionRecord,
    mode_family: str,
    supports_grid: bool,
    mode_registry: ModeRegistry | None = None,
) -> tuple[EditorAction, ...]:
    """Build artifact and overview dashboard actions."""

    actions = list(_overview_actions(item, session, mode_family, supports_grid))
    actions.extend(_artifact_repair_actions_for_session(item, session, mode_registry))
    return tuple(actions)


def _overview_actions(
    item: SessionItem,
    session: SessionRecord,
    mode_family: str,
    supports_grid: bool,
) -> tuple[EditorAction, ...]:
    actions = [
        _action(
            EditorActionType.GENERATE_SESSION_OVERVIEW,
            "Generate Session Overview",
            item.item_id,
        )
    ]
    if session_mode_value(session.mode) == "fast_batch_capture":
        actions.append(_action(EditorActionType.BATCH_RENAME, "Batch Rename", item.item_id))
    if mode_family == "metrology":
        actions.append(
            _action(
                EditorActionType.GENERATE_METROLOGY_OVERVIEW,
                "Generate Metrology Overview",
                item.item_id,
            )
        )
    if supports_grid:
        enabled, disabled_reason = _grid_creation_availability(session)
        actions.append(
            _action(
                EditorActionType.CREATE_GRID_DATASET,
                "Create Grid Dataset",
                item.item_id,
                enabled=enabled,
                disabled_reason=disabled_reason,
            )
        )
        actions.append(
            _action(
                EditorActionType.GENERATE_GRID_OVERVIEW,
                "Generate Grid Overview",
                item.item_id,
            )
        )
    return tuple(actions)


def _action(
    action_type: EditorActionType,
    label: str,
    item_id: str,
    *,
    enabled: bool = True,
    disabled_reason: str = "",
) -> EditorAction:
    return EditorAction(
        action_type,
        label,
        item_id,
        enabled=enabled,
        disabled_reason=disabled_reason,
    )


def _grid_creation_availability(session: SessionRecord) -> tuple[bool, str]:
    if len(_box_captures(session.captures)) >= 2:
        return True, ""
    return False, "Grid datasets require at least two saved box captures."


def _box_captures(captures: tuple[CaptureRecord, ...]) -> tuple[CaptureRecord, ...]:
    return tuple(capture for capture in captures if capture.geometry.bounds is not None)


def _artifact_repair_actions_for_session(
    item: SessionItem,
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[EditorAction, ...]:
    missing_count = _visible_artifact_status_count(session, "missing", mode_registry)
    stale_count = _visible_artifact_status_count(session, "stale", mode_registry)
    return (
        EditorAction(EditorActionType.ADD_USER_LABEL, "Add User Label", item.item_id),
        EditorAction(EditorActionType.SCAN_ARTIFACTS, "Scan Artifacts", item.item_id),
        EditorAction(
            EditorActionType.REGENERATE_MISSING_ARTIFACTS,
            "Regenerate Missing",
            item.item_id,
            enabled=missing_count != 0,
            disabled_reason=(
                "" if missing_count != 0 else "No visible missing artifacts need repair."
            ),
        ),
        EditorAction(
            EditorActionType.REGENERATE_STALE_ARTIFACTS,
            "Regenerate Stale",
            item.item_id,
            enabled=stale_count != 0,
            disabled_reason=(
                "" if stale_count != 0 else "No visible stale artifacts need repair."
            ),
        ),
        EditorAction(
            EditorActionType.EXPORT_ARTIFACT_MANIFEST,
            "Export Artifact Manifest",
            item.item_id,
        ),
    )


def _visible_artifact_status_count(
    session: SessionRecord,
    status: str,
    mode_registry: ModeRegistry | None,
) -> int:
    return sum(
        1
        for artifact in visible_dashboard_artifacts(session, mode_registry)
        if artifact.status.value == status
    )


def _mode_is_process_aware(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> bool:
    mode = (mode_registry or built_in_mode_registry()).definition(session.mode.value)
    return (
        mode.family == "process_aware"
        or mode.capabilities.supports_process_solver
        or mode.process.recipe_policy not in {"forbidden", "optional_hidden"}
    )
