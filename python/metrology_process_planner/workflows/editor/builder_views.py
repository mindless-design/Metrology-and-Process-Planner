"""Shared view helpers for normalized editor document building."""

from __future__ import annotations

from collections.abc import Mapping

from metrology_process_planner.domains.session import SessionRecord
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

GROUP_ORDER: tuple[tuple[SessionItemKind, str], ...] = (
    (SessionItemKind.DASHBOARD, "Dashboard"),
    (SessionItemKind.SETUP, "Setup"),
    (SessionItemKind.PENDING_CAPTURE, "Pending"),
    (SessionItemKind.SAVED_CAPTURE, "Saved Captures"),
    (SessionItemKind.FEATURE, "Features"),
    (SessionItemKind.MEASUREMENT, "Measurements"),
    (SessionItemKind.GRID_DATASET, "Grid Datasets"),
    (SessionItemKind.CROSS_SECTION, "Cross Sections"),
    (SessionItemKind.REPORT, "Reports"),
    (SessionItemKind.WARNING, "Warnings"),
)


def _simple_item(item_id: str, kind: SessionItemKind, label: str) -> SessionItem:
    return SessionItem(item_id=item_id, kind=kind, label=label, role=kind.value)


def _grid_item(session: SessionRecord, dataset_id: str, label: str) -> SessionItem:
    return SessionItem(
        item_id=f"grid:{dataset_id}",
        kind=SessionItemKind.GRID_DATASET,
        label=label,
        role="grid_dataset",
        record_ref=RecordRef("grid_dataset", dataset_id),
        artifact_refs=_artifact_refs_for_owner(session, "grid_dataset", dataset_id),
    )


def _report_item(session: SessionRecord, report_id: str, label: str) -> SessionItem:
    return SessionItem(
        item_id=f"report:{report_id}",
        kind=SessionItemKind.REPORT,
        label=label,
        role="report",
        record_ref=RecordRef("report", report_id),
        artifact_refs=_artifact_refs_for_owner(session, "report", report_id),
    )


def _process_output_item(session: SessionRecord, output_id: str, label: str) -> SessionItem:
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


def _warning_view_models(session: SessionRecord) -> tuple[WarningViewModel, ...]:
    return tuple(
        WarningViewModel(
            warning_id=warning.id,
            message=warning.message,
            severity=warning.severity,
            item_id=_first_related_item(warning.related_item_refs),
            artifact_path=warning.artifact_path or "",
        )
        for warning in session.warnings
    )


def _first_related_item(related: tuple[str, ...]) -> str:
    return related[0] if related else ""


def _groups(items: Mapping[str, SessionItem]) -> tuple[SessionItemGroup, ...]:
    groups = []
    for kind, label in GROUP_ORDER:
        item_ids = tuple(item.item_id for item in items.values() if item.kind is kind)
        if item_ids:
            groups.append(SessionItemGroup(kind.value, label, item_ids))
    return tuple(groups)
