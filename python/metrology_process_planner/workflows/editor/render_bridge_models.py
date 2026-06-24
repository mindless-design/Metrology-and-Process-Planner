"""Typed request and result contracts for editor/rendering refresh."""

from __future__ import annotations

from dataclasses import dataclass

from metrology_process_planner.domains.process import CrossSectionProfile, Material
from metrology_process_planner.domains.session import SessionRecord, WarningRecord


@dataclass(frozen=True)
class DrawingOwnerRef:
    """Stable owner for a drawing refresh target."""

    owner_type: str
    owner_id: str


@dataclass(frozen=True)
class RenderTarget:
    """One persisted drawing target to refresh."""

    owner: DrawingOwnerRef
    role: str = "layout_annotation"


@dataclass(frozen=True)
class CrossSectionRenderInput:
    """Inputs required to render and persist a cross-section drawing."""

    owner: DrawingOwnerRef
    profile: CrossSectionProfile
    materials: tuple[Material, ...]
    title: str = ""
    scene_id: str = ""
    include_legend: bool = True


@dataclass(frozen=True)
class RenderRefreshRequest:
    """Batch of editor/rendering refresh work."""

    targets: tuple[RenderTarget, ...] = ()
    cross_sections: tuple[CrossSectionRenderInput, ...] = ()
    refresh_all_captures: bool = False
    refresh_all_measurements: bool = False


@dataclass(frozen=True)
class RenderRefreshResult:
    """Session and status returned after a render refresh."""

    status: str
    session: SessionRecord
    message: str = ""
    updated_artifact_paths: tuple[str, ...] = ()
    warnings: tuple[WarningRecord, ...] = ()
