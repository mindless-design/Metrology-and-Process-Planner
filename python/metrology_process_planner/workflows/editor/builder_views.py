"""Shared view helpers for normalized editor document building."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.builder_artifact_refs import (
    _artifact_refs_by_id,
    _artifact_refs_for_owner,
)
from metrology_process_planner.workflows.editor.document import (
    SessionItem,
    SessionItemGroup,
    SessionItemKind,
)
from metrology_process_planner.workflows.editor.references import RecordRef
from metrology_process_planner.workflows.editor.view_models import WarningViewModel
from metrology_process_planner.workflows.editor.warning_visibility import editor_visible_warnings

GROUP_ORDER: tuple[tuple[SessionItemKind, str], ...] = (
    (SessionItemKind.DASHBOARD, "Dashboard"),
    (SessionItemKind.SETUP, "Setup"),
    (SessionItemKind.PENDING_CAPTURE, "Pending"),
    (SessionItemKind.SAVED_CAPTURE, "Saved Captures"),
    (SessionItemKind.FEATURE, "Features"),
    (SessionItemKind.MEASUREMENT, "Measurements"),
    (SessionItemKind.GRID_DATASET, "Grid Datasets"),
    (SessionItemKind.OVERVIEW, "Overviews / Maps"),
    (SessionItemKind.CROSS_SECTION, "Cross Sections"),
    (SessionItemKind.REPORT, "Reports"),
    (SessionItemKind.WARNING, "Warnings"),
)

GROUP_ID_KIND_ALIASES: Mapping[str, tuple[SessionItemKind, ...]] = {
    "dashboard": (SessionItemKind.DASHBOARD,),
    "setup": (SessionItemKind.SETUP,),
    "pending": (SessionItemKind.PENDING_CAPTURE,),
    "pending_captures": (SessionItemKind.PENDING_CAPTURE,),
    "captures": (SessionItemKind.SAVED_CAPTURE,),
    "saved_captures": (SessionItemKind.SAVED_CAPTURE,),
    "features": (SessionItemKind.FEATURE,),
    "measurements": (SessionItemKind.MEASUREMENT,),
    "grid_datasets": (SessionItemKind.GRID_DATASET,),
    "overviews": (SessionItemKind.OVERVIEW,),
    "overview": (SessionItemKind.OVERVIEW,),
    "reports": (SessionItemKind.REPORT,),
    "warnings": (SessionItemKind.WARNING,),
    "process_outputs": (SessionItemKind.CROSS_SECTION,),
    "cross_sections": (SessionItemKind.CROSS_SECTION,),
}


def _simple_item(item_id: str, kind: SessionItemKind, label: str) -> SessionItem:
    return SessionItem(item_id=item_id, kind=kind, label=label, role=kind.value)


def _grid_item(
    session: SessionRecord,
    dataset_id: str,
    label: str,
    mode_registry: ModeRegistry | None = None,
) -> SessionItem:
    return SessionItem(
        item_id=f"grid:{dataset_id}",
        kind=SessionItemKind.GRID_DATASET,
        label=label,
        role="grid_dataset",
        record_ref=RecordRef("grid_dataset", dataset_id),
        artifact_refs=_artifact_refs_for_owner(session, "grid_dataset", dataset_id, mode_registry),
    )


def _report_item(
    session: SessionRecord,
    report_id: str,
    label: str,
    mode_registry: ModeRegistry | None = None,
) -> SessionItem:
    return SessionItem(
        item_id=f"report:{report_id}",
        kind=SessionItemKind.REPORT,
        label=label,
        role="report",
        record_ref=RecordRef("report", report_id),
        artifact_refs=_artifact_refs_for_owner(session, "report", report_id, mode_registry),
    )


def _overview_item(
    session: SessionRecord,
    role: str,
    label: str,
    mode_registry: ModeRegistry | None = None,
) -> SessionItem:
    return SessionItem(
        item_id=f"overview:{role}",
        kind=SessionItemKind.OVERVIEW,
        label=label,
        role=role,
        record_ref=RecordRef("session_overview", role),
        artifact_refs=tuple(
            ref
            for ref in _artifact_refs_for_owner(session, "session", session.id, mode_registry)
            if ref.role == role
        ),
    )


def _process_output_item(
    session: SessionRecord,
    output_id: str,
    label: str,
    mode_registry: ModeRegistry | None = None,
) -> SessionItem:
    output = next(item for item in session.process_outputs if item.id == output_id)
    return SessionItem(
        item_id=f"process_output:{output_id}",
        kind=SessionItemKind.CROSS_SECTION,
        label=label,
        role="process_output",
        record_ref=RecordRef("process_output", output_id),
        artifact_refs=_artifact_refs_by_id(
            session,
            dict(output.artifact_refs or {}),
            "process_output",
            mode_registry,
        ),
    )


def _warning_item(warning: WarningViewModel) -> SessionItem:
    return SessionItem(
        item_id=f"warning:{warning.warning_id}",
        kind=SessionItemKind.WARNING,
        label=warning.message,
        role="warning",
        status=warning.severity,
        parent_id=warning.item_id or None,
        record_ref=RecordRef("warning", warning.warning_id),
        warning_ids=(warning.warning_id,),
    )


def _warning_view_models(
    session: SessionRecord,
    mode_registry: ModeRegistry | None = None,
) -> tuple[WarningViewModel, ...]:
    return tuple(
        WarningViewModel(
            warning_id=warning.id,
            message=warning.message,
            severity=warning.severity,
            item_id=_first_related_item(warning.related_item_refs),
            artifact_path=warning.artifact_path or "",
        )
        for warning in editor_visible_warnings(session, mode_registry)
    )


def _first_related_item(related: tuple[str, ...]) -> str:
    return related[0] if related else ""


def _groups(
    items: Mapping[str, SessionItem],
    navigator_group_ids: tuple[str, ...] = (),
) -> tuple[SessionItemGroup, ...]:
    allowed_kinds = _allowed_group_kinds(navigator_group_ids)
    groups = []
    for kind, label in GROUP_ORDER:
        if allowed_kinds is not None and kind not in allowed_kinds:
            continue
        item_ids = tuple(item.item_id for item in items.values() if item.kind is kind)
        if item_ids:
            groups.append(SessionItemGroup(kind.value, label, item_ids))
    return tuple(groups)


def _allowed_group_kinds(group_ids: tuple[str, ...]) -> set[SessionItemKind] | None:
    if not group_ids:
        return None
    allowed: set[SessionItemKind] = set()
    for group_id in group_ids:
        allowed.update(GROUP_ID_KIND_ALIASES.get(group_id, ()))
    return allowed
