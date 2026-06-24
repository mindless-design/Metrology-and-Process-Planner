"""Refresh loop helpers for the editor render bridge."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from metrology_process_planner.domains.session import SessionRecord, WarningRecord
from metrology_process_planner.workflows.editor.render_bridge_measurements import (
    refresh_measurement_target,
)
from metrology_process_planner.workflows.editor.render_bridge_models import (
    CrossSectionRenderInput,
    DrawingOwnerRef,
    RenderRefreshRequest,
    RenderRefreshResult,
    RenderTarget,
)
from metrology_process_planner.workflows.editor.render_bridge_ops import (
    refresh_cross_section,
    refresh_target,
)

if TYPE_CHECKING:
    from metrology_process_planner.workflows.editor.render_bridge import SessionRenderBridge


@dataclass(frozen=True)
class RefreshState:
    """Aggregate state for one render bridge refresh request."""

    session: SessionRecord
    updated_paths: tuple[str, ...] = ()
    warnings: tuple[WarningRecord, ...] = ()
    had_error: bool = False
    had_warning: bool = False

    @property
    def status(self) -> str:
        """Return the aggregate refresh status."""

        if self.had_error:
            return "error"
        return "warning" if self.had_warning else "success"

    def add(self, result: RenderRefreshResult) -> RefreshState:
        """Return state updated with one target refresh result."""

        return RefreshState(
            session=result.session,
            updated_paths=self.updated_paths + result.updated_artifact_paths,
            warnings=self.warnings + result.warnings,
            had_error=self.had_error or result.status == "error",
            had_warning=self.had_warning or result.status == "warning",
        )


def refresh_request_targets(
    bridge: SessionRenderBridge,
    session: SessionRecord,
    request: RenderRefreshRequest,
) -> RefreshState:
    """Refresh ordinary and cross-section targets for one request."""

    state = _refresh_targets(bridge, session, _expanded_targets(session, request))
    return _refresh_cross_sections(bridge, state, request.cross_sections)


def _expanded_targets(
    session: SessionRecord,
    request: RenderRefreshRequest,
) -> tuple[RenderTarget, ...]:
    targets = list(request.targets)
    if request.refresh_all_captures:
        targets.extend(
            RenderTarget(DrawingOwnerRef("capture", capture.id), "layout_annotation")
            for capture in session.captures
        )
    if request.refresh_all_measurements:
        targets.extend(_measurement_targets(session))
    return _unique_targets(targets)


def _refresh_targets(
    bridge: SessionRenderBridge,
    session: SessionRecord,
    targets: Iterable[RenderTarget],
) -> RefreshState:
    state = RefreshState(session)
    for target in targets:
        state = state.add(_refresh_target(bridge, state.session, target))
    return state


def _refresh_cross_sections(
    bridge: SessionRenderBridge,
    state: RefreshState,
    cross_sections: Iterable[CrossSectionRenderInput],
) -> RefreshState:
    for cross_section in cross_sections:
        state = state.add(refresh_cross_section(bridge, state.session, cross_section))
    return state


def _unique_targets(targets: Iterable[RenderTarget]) -> tuple[RenderTarget, ...]:
    seen: set[tuple[str, str, str]] = set()
    unique = []
    for target in targets:
        key = (target.owner.owner_type, target.owner.owner_id, target.role)
        if key not in seen:
            seen.add(key)
            unique.append(target)
    return tuple(unique)


def _measurement_targets(session: SessionRecord) -> tuple[RenderTarget, ...]:
    return tuple(
        RenderTarget(DrawingOwnerRef("measurement", measurement.id), "measurement_annotation")
        for capture in session.captures
        for measurement in capture.measurements
    )


def _refresh_target(
    bridge: SessionRenderBridge,
    session: SessionRecord,
    target: RenderTarget,
) -> RenderRefreshResult:
    if target.owner.owner_type == "measurement":
        return refresh_measurement_target(bridge, session, target)
    return refresh_target(bridge, session, target)
