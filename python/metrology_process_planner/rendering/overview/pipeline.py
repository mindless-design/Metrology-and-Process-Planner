"""High-level overview diagram generation pipeline."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.rendering.overview.artifacts import (
    overview_warnings,
    write_overview_artifact,
)
from metrology_process_planner.rendering.overview.content import build_label_content
from metrology_process_planner.rendering.overview.extraction import extract_label_targets
from metrology_process_planner.rendering.overview.layout import OverviewLayoutPlanner
from metrology_process_planner.rendering.overview.models import (
    LabelPlacementPolicy,
    OverviewDiagramRequest,
    OverviewDiagramScene,
)
from metrology_process_planner.rendering.overview.renderer import OverviewDiagramRenderer


def build_overview_scene(
    session: SessionRecord,
    request: OverviewDiagramRequest | None = None,
) -> OverviewDiagramScene:
    """Run target extraction, content generation, placement, and leader routing."""

    request = request or default_overview_request(session)
    policy = request.placement_policy or LabelPlacementPolicy()
    targets = extract_label_targets(session)
    detail_level = str((request.label_policy or {}).get("detail_level", "standard"))
    contents = build_label_content(targets, detail_level)
    title = str((request.output_spec or {}).get("title", "Session Overview"))
    return OverviewLayoutPlanner().plan(request.request_id, targets, contents, policy, title)


def generate_overview_artifact(
    session: SessionRecord,
    output_folder: Path,
    request: OverviewDiagramRequest | None = None,
) -> SessionRecord:
    """Generate an overview SVG artifact and return an updated session record."""

    request = request or default_overview_request(session)
    scene = build_overview_scene(session, request)
    svg_text = OverviewDiagramRenderer().render_svg(scene, request.style_policy)
    artifact = write_overview_artifact(
        session,
        request.artifact_role,
        svg_text,
        scene,
        output_folder,
    )
    artifacts = dict(session.artifacts or {})
    artifacts[artifact.id] = artifact
    warnings = tuple(
        warning
        for warning in session.warnings
        if not warning.id.startswith(f"warning-{artifact.id}-")
    )
    warnings += overview_warnings(artifact, scene)
    return replace(session, artifacts=artifacts, warnings=warnings)


def default_overview_request(
    session: SessionRecord,
    role: str = "session_overview",
) -> OverviewDiagramRequest:
    """Return the default session overview request."""

    return OverviewDiagramRequest(
        request_id=f"{session.id}-{role}",
        session_id=session.id,
        source_layout_ref=session.source_layout.layout_path,
        artifact_role=role,
    )
