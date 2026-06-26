"""Build normalized editor documents from canonical session records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any, Optional

from metrology_process_planner.domains.session import ModeRegistry, SessionRecord
from metrology_process_planner.workflows.editor.builder_artifact_health import (
    artifact_details,
    artifact_health,
)
from metrology_process_planner.workflows.editor.builder_basics import (
    dashboard_item,
    mode_is_process_aware,
    mode_uses_setup,
    setup_item,
)
from metrology_process_planner.workflows.editor.builder_canvas import pending_canvas_ids
from metrology_process_planner.workflows.editor.builder_drawings import (
    artifact_owned_drawing_items,
)
from metrology_process_planner.workflows.editor.builder_features import (
    feature_items_for_capture,
)
from metrology_process_planner.workflows.editor.builder_measurements import measurement_item_for
from metrology_process_planner.workflows.editor.builder_overviews import overview_roles
from metrology_process_planner.workflows.editor.builder_record_items import (
    capture_item,
    pending_item,
)
from metrology_process_planner.workflows.editor.builder_views import (
    _grid_item,
    _groups,
    _overview_item,
    _process_output_item,
    _report_item,
    _warning_item,
    _warning_view_models,
)
from metrology_process_planner.workflows.editor.document import (
    EditorSelectionState,
    SessionDocument,
    SessionItem,
)
from metrology_process_planner.workflows.editor.view_models import WarningViewModel


class SessionDocumentBuilder:
    """Build a normalized session editor document and item indexes."""

    def __init__(self, mode_registry: ModeRegistry | None = None) -> None:
        self._mode_registry = mode_registry

    def build(
        self,
        session: SessionRecord,
        raw_payload: Optional[Mapping[str, Any]] = None,
    ) -> SessionDocument:
        """Return an editor document for a canonical session record."""

        warnings = _warning_view_models(session, self._mode_registry)
        warning_artifacts = {
            warning.artifact_path: warning for warning in warnings if warning.artifact_path
        }
        items = _attach_children(
            _session_items(session, warnings, warning_artifacts, self._mode_registry)
        )
        selected = _default_selection(session)
        return SessionDocument(
            session=session,
            raw_payload=dict(raw_payload or {}),
            items_by_id=items,
            root_item_ids=tuple(items),
            navigator_groups=_groups(items, _navigator_group_ids(session, self._mode_registry)),
            selection=selected,
            warning_view_models=warnings,
            artifact_health=artifact_health(session, self._mode_registry),
            artifact_details_by_item_id=artifact_details(items, session, self._mode_registry),
            pending_capture_item_id=selected.selected_item_id if session.pending_captures else None,
        )


def _add(items: dict[str, SessionItem], item: SessionItem) -> None:
    items[item.item_id] = item


def _navigator_group_ids(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[str, ...]:
    if mode_registry is None:
        from metrology_process_planner.domains.session import built_in_mode_registry

        mode_registry = built_in_mode_registry()
    return mode_registry.definition(session.mode.value).editor.navigator_groups


def _session_items(
    session: SessionRecord,
    warnings: tuple[WarningViewModel, ...],
    warning_artifacts: Mapping[str, WarningViewModel],
    mode_registry: ModeRegistry | None,
) -> dict[str, SessionItem]:
    items: dict[str, SessionItem] = {}
    _add(items, dashboard_item(session))
    if mode_uses_setup(session, mode_registry):
        _add(items, setup_item(session, mode_registry))
    _add_record_items(items, session, warning_artifacts, mode_registry)
    for warning in warnings:
        _add(items, _warning_item(warning))
    return items


def _add_record_items(
    items: dict[str, SessionItem],
    session: SessionRecord,
    warning_artifacts: Mapping[str, WarningViewModel],
    mode_registry: ModeRegistry | None,
) -> None:
    for item in _record_items(session, warning_artifacts, mode_registry):
        _add(items, item)


def _record_items(
    session: SessionRecord,
    warning_artifacts: Mapping[str, WarningViewModel],
    mode_registry: ModeRegistry | None,
) -> tuple[SessionItem, ...]:
    items: list[SessionItem] = []
    items.extend(_pending_items(session, warning_artifacts, mode_registry))
    items.extend(_capture_items(session, mode_registry))
    for dataset in session.grid_datasets:
        items.append(_grid_item(session, dataset.id, dataset.label, mode_registry))
    items.extend(artifact_owned_drawing_items(session, mode_registry))
    for role in overview_roles(session, mode_registry):
        items.append(_overview_item(session, role, role.replace("_", " ").title(), mode_registry))
    for report in session.reports:
        items.append(
            _report_item(session, report.id, report.label or report.report_type, mode_registry)
        )
    if mode_is_process_aware(session, mode_registry):
        items.extend(
            _process_output_item(session, output.id, output.label, mode_registry)
            for output in session.process_outputs
        )
    return tuple(items)


def _pending_items(
    session: SessionRecord,
    warning_artifacts: Mapping[str, WarningViewModel],
    mode_registry: ModeRegistry | None,
) -> tuple[SessionItem, ...]:
    return tuple(
        pending_item(session, pending.id, warning_artifacts, mode_registry)
        for pending in session.pending_captures
    )


def _capture_items(
    session: SessionRecord,
    mode_registry: ModeRegistry | None,
) -> tuple[SessionItem, ...]:
    items: list[SessionItem] = []
    for capture in session.captures:
        items.append(capture_item(session, capture, mode_registry))
        items.extend(feature_items_for_capture(session, capture, mode_registry))
        items.extend(
            measurement_item_for(session, capture.id, measurement, mode_registry)
            for measurement in capture.measurements
        )
    return tuple(items)


def _attach_children(items: dict[str, SessionItem]) -> dict[str, SessionItem]:
    child_map: dict[str, list[str]] = {}
    for item in items.values():
        if item.parent_id:
            child_map.setdefault(item.parent_id, []).append(item.item_id)
    return {
        item_id: replace(item, child_ids=tuple(child_map.get(item_id, ())))
        for item_id, item in items.items()
    }


def _default_selection(session: SessionRecord) -> EditorSelectionState:
    if session.pending_captures:
        pending = session.pending_captures[0]
        return EditorSelectionState(
            selected_item_id=f"pending:{pending.id}",
            selected_canvas_object_ids=pending_canvas_ids(session, pending.canvas_object_id),
        )
    return EditorSelectionState()
