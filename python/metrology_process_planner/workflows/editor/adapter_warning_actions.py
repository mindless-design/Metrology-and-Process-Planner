"""Warning-derived editor repair actions."""

from __future__ import annotations

from metrology_process_planner.domains.artifacts.artifact_visibility import (
    artifact_visible_for_session,
)
from metrology_process_planner.domains.session import ModeRegistry, SessionRecord, WarningRecord
from metrology_process_planner.workflows.editor.adapter_artifact_actions import (
    artifact_warning_action,
)
from metrology_process_planner.workflows.editor.builder_basics import mode_is_process_aware
from metrology_process_planner.workflows.editor.document import SessionItem
from metrology_process_planner.workflows.editor.view_models import EditorAction, EditorActionType

_RECIPE_CODES = frozenset(
    {
        "PROCESS_RECIPE_MISSING",
        "PROCESS_RECIPE_FILE_NOT_FOUND",
        "PROCESS_RECIPE_PARSE_FAILED",
        "PROCESS_RECIPE_FINGERPRINT_MISMATCH",
    }
)
_PROCESS_CODES = _RECIPE_CODES | frozenset(
    {
        "SOLVER_BACKEND_UNAVAILABLE",
        "RENDER_PROFILE_MISSING",
        "PROCESS_OUTPUT_STALE",
        "PROCESS_OUTPUT_REGENERATION_FAILED",
    }
)


def warning_actions(
    session: SessionRecord,
    item: SessionItem,
    mode_registry: ModeRegistry | None = None,
) -> tuple[EditorAction, ...]:
    """Return editor repair actions for a warning item."""

    warning = _warning_for_item(session, item)
    if warning is None:
        return ()
    actions: list[EditorAction] = []
    if warning.status == "open":
        actions.append(
            EditorAction(EditorActionType.IGNORE_WARNING, "Ignore Warning", item.item_id)
        )
    actions.extend(_artifact_warning_actions(session, item, warning, mode_registry))
    if (
        mode_is_process_aware(session, mode_registry)
        and (warning.code in _PROCESS_CODES or warning.source == "process_context")
    ):
        actions.extend(_process_warning_actions(session, warning))
    return _dedupe(actions)


def _artifact_warning_actions(
    session: SessionRecord,
    item: SessionItem,
    warning: WarningRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[EditorAction, ...]:
    artifact_ids = _warning_artifact_ids(warning)
    if not artifact_ids:
        return ()
    actions: list[EditorAction] = []
    artifacts = session.artifacts or {}
    for artifact_id in artifact_ids:
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            continue
        if not artifact_visible_for_session(session, artifact, mode_registry):
            continue
        if artifact.repair.regenerable:
            actions.append(
                artifact_warning_action(
                    EditorActionType.REGENERATE_ARTIFACT,
                    "Regenerate Artifact",
                    item.item_id,
                    artifact_id,
                    warning.id,
                )
            )
        if warning.code in {"ARTIFACT_MISSING", "ARTIFACT_RELINK_REQUIRED"}:
            actions.append(
                artifact_warning_action(
                    EditorActionType.RELINK_ARTIFACT,
                    "Relink Artifact",
                    item.item_id,
                    artifact_id,
                    warning.id,
                )
            )
    return tuple(actions)


def _process_warning_actions(
    session: SessionRecord,
    warning: WarningRecord,
) -> tuple[EditorAction, ...]:
    target = _capture_item_ref(warning) or "dashboard"
    actions = [
        EditorAction(EditorActionType.VALIDATE_PROCESS_CONTEXT, "Validate Process Context", target)
    ]
    if warning.code in _RECIPE_CODES:
        actions.insert(0, EditorAction(EditorActionType.ATTACH_RECIPE, "Attach Recipe", target))
    if session.process_context.recipe_path:
        actions.append(
            EditorAction(
                EditorActionType.OPEN_RECIPE_FILE,
                "Open Recipe File",
                "dashboard",
                payload=(("recipe_path", session.process_context.recipe_path),),
            )
        )
    if target.startswith("capture:") or warning.code in _output_codes():
        actions.append(
            EditorAction(
                EditorActionType.REGENERATE_PROCESS_OUTPUT,
                "Regenerate Process Output",
                target,
            )
        )
    return tuple(actions)


def _warning_for_item(session: SessionRecord, item: SessionItem) -> WarningRecord | None:
    warning_id = item.warning_ids[0] if item.warning_ids else ""
    if not warning_id and item.record_ref is not None and item.record_ref.record_type == "warning":
        warning_id = item.record_ref.record_id
    for warning in session.warnings:
        if warning.id == warning_id:
            return warning
    return None


def _warning_artifact_ids(warning: WarningRecord) -> tuple[str, ...]:
    if warning.source == "artifact" or warning.related_artifact_refs:
        return warning.related_artifact_refs
    return ()


def _capture_item_ref(warning: WarningRecord) -> str:
    for ref in warning.related_item_refs:
        if ref.startswith("capture:"):
            return ref
    return ""


def _output_codes() -> frozenset[str]:
    return frozenset(
        {
            "SOLVER_BACKEND_UNAVAILABLE",
            "PROCESS_OUTPUT_STALE",
            "PROCESS_OUTPUT_REGENERATION_FAILED",
        }
    )


def _dedupe(actions: list[EditorAction]) -> tuple[EditorAction, ...]:
    seen: set[tuple[EditorActionType, str, tuple[tuple[str, str], ...]]] = set()
    unique: list[EditorAction] = []
    for action in actions:
        key = (action.action_type, action.item_id, action.payload)
        if key not in seen:
            seen.add(key)
            unique.append(action)
    return tuple(unique)
