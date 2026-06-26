"""Concrete headless artifact generator handlers."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.artifacts.artifact_content import artifact_content_type
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactRecord,
    ArtifactStatus,
    ModeRegistry,
    SessionRecord,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.persistence.process_output_store import ProcessOutputStore
from metrology_process_planner.rendering.overview import (
    default_overview_request,
    generate_overview_artifact,
)
from metrology_process_planner.rendering.theme import render_theme
from metrology_process_planner.workflows.artifacts.generators import ArtifactGenerationResult
from metrology_process_planner.workflows.editor.csv_export_artifacts import (
    with_csv_export_artifact,
)
from metrology_process_planner.workflows.editor.render_bridge import SessionRenderBridge
from metrology_process_planner.workflows.editor.render_bridge_models import (
    DrawingOwnerRef,
    RenderRefreshRequest,
    RenderTarget,
)
from metrology_process_planner.workflows.process_context import regenerate_process_outputs
from metrology_process_planner.workflows.process_context_models import (
    RegenerateProcessOutputsCommand,
)


def rebuild_csv_export(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
    mode_registry: ModeRegistry | None = None,
) -> ArtifactGenerationResult:
    """Rebuild the canonical capture CSV and return its registry record."""

    destination = CaptureCsvExporter(mode_registry=mode_registry).export(session, paths.capture_csv)
    updated = with_csv_export_artifact(session, paths, destination, mode_registry)
    generated = _generated_artifact(updated, artifact) or artifact
    return ArtifactGenerationResult(generated, updated)


def write_placeholder_image(
    _session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
) -> ArtifactRecord:
    """Write a visible SVG placeholder for a blocked or missing image artifact."""

    relative_path = artifact.relative_path or f"artifacts/placeholders/{artifact.id}.svg"
    destination = artifact_path_to_disk(paths.folder, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_placeholder_svg(artifact), encoding="utf-8")
    return replace(
        artifact,
        relative_path=relative_path,
        status=ArtifactStatus.PRESENT,
        file=ArtifactFileMetadata(
            width_px=640,
            height_px=360,
            content_type=artifact_content_type(relative_path) or "image/svg+xml",
        ),
        warning_ids=(),
    )


def refresh_measurement_annotation(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
) -> ArtifactGenerationResult:
    """Regenerate a measurement annotation through the editor render bridge."""

    result = SessionRenderBridge(paths).refresh(
        session,
        RenderRefreshRequest(
            targets=(
                RenderTarget(
                    DrawingOwnerRef("measurement", artifact.owner.owner_id),
                    "measurement_annotation",
                ),
            ),
        ),
    )
    generated = _generated_artifact(result.session, artifact)
    if generated is None:
        raise RuntimeError(f"Generator did not produce artifact {artifact.id}.")
    return ArtifactGenerationResult(generated, result.session)


def regenerate_overview(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
) -> ArtifactGenerationResult:
    """Regenerate an overview diagram artifact from durable session records."""

    role = artifact.owner.role or "session_overview"
    request = default_overview_request(session, role)
    updated = generate_overview_artifact(session, paths.folder, request)
    generated = _generated_artifact(updated, artifact)
    if generated is None:
        raise RuntimeError(f"Generator did not produce overview artifact {artifact.id}.")
    return ArtifactGenerationResult(generated, updated)


def regenerate_process_output_artifact(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
) -> ArtifactGenerationResult:
    """Regenerate and export process-output artifacts for the owning capture."""

    owner_id = artifact.owner.owner_id
    result = regenerate_process_outputs(session, RegenerateProcessOutputsCommand(owner_id))
    if result.status != "success":
        raise RuntimeError(result.message or "Process output regeneration did not complete.")
    updated = ProcessOutputStore().export_ready_outputs(paths, result.session, owner_id)
    generated = _generated_artifact(updated, artifact)
    if generated is None:
        raise RuntimeError(f"Generator did not produce process artifact {artifact.id}.")
    return ArtifactGenerationResult(generated, updated)


def _generated_artifact(
    session: SessionRecord,
    artifact: ArtifactRecord,
) -> ArtifactRecord | None:
    artifacts = session.artifacts or {}
    if artifact.id in artifacts:
        return artifacts[artifact.id]
    for candidate in artifacts.values():
        if (
            candidate.owner.owner_type == artifact.owner.owner_type
            and candidate.owner.owner_id == artifact.owner.owner_id
            and candidate.owner.role == artifact.owner.role
        ):
            return candidate
    return None


def _placeholder_svg(artifact: ArtifactRecord) -> str:
    title = _escape(artifact.label or artifact.id)
    detail = _escape(artifact.repair.placeholder_reason or "Artifact placeholder")
    theme = render_theme("engineering_dark")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" '
        'viewBox="0 0 640 360" role="img">'
        f'<rect width="640" height="360" fill="{theme.background}"/>'
        '<rect x="24" y="24" width="592" height="312" fill="none" '
        f'stroke="{theme.panel_stroke}" stroke-width="2" stroke-dasharray="8 6"/>'
        f'<text x="320" y="166" text-anchor="middle" '
        f'font-family="Arial, sans-serif" font-size="24" fill="{theme.primary_text}">{title}</text>'
        f'<text x="320" y="206" text-anchor="middle" '
        f'font-family="Arial, sans-serif" font-size="15" '
        f'fill="{theme.secondary_text}">{detail}</text>'
        "</svg>"
    )


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
