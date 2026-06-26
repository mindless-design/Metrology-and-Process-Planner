"""Artifact registry integration helpers for rendered cross-section outputs."""

from __future__ import annotations

from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    WarningRecord,
    artifact_id,
)
from metrology_process_planner.rendering.cross_section.models import CrossSectionRenderResult
from metrology_process_planner.rendering.cross_section.scene_models import CrossSectionSceneModel

RENDER_WARNING_CODES = (
    "RENDER_PROFILE_MISSING",
    "RENDER_FEATURE_FILTER_EMPTY",
    "RENDER_GEOMETRY_TOO_SMALL",
    "RENDER_THIN_LAYER_EXAGGERATED",
    "RENDER_COMPRESSION_APPLIED",
    "RENDER_SIMPLIFICATION_APPLIED",
    "RENDER_LABEL_COLLISION_UNRESOLVED",
    "RENDER_EXPORT_FAILED",
    "RENDER_BACKEND_UNAVAILABLE",
)


def build_render_artifact_record(
    owner_type: str,
    owner_id: str,
    role: str,
    artifact_type: str,
    relative_path: str,
    scene: CrossSectionSceneModel,
    render_result: CrossSectionRenderResult | None = None,
) -> ArtifactRecord:
    """Create a central artifact record carrying render metadata."""

    record_id = render_result.artifact_id if render_result and render_result.artifact_id else (
        artifact_id(owner_type, owner_id, role)
    )
    status = ArtifactStatus.PRESENT
    if render_result and render_result.status not in {"success", "warning"}:
        status = ArtifactStatus.FAILED
    return ArtifactRecord(
        record_id,
        artifact_type,
        scene.title,
        relative_path,
        ArtifactOwnerRef(owner_type, owner_id, role),
        status=status,
        generator="CrossSectionRenderingPipeline/1",
        file=_file_metadata(render_result),
        repair=ArtifactRepairMetadata("regenerate_process_output", "Regenerate process output."),
        warning_ids=(),
        extensions=_artifact_extensions(scene, render_result),
    )


def build_failed_render_warning(
    owner_id: str,
    artifact: ArtifactRecord,
    code: str,
    message: str,
    technical_details: str = "",
) -> WarningRecord:
    """Create a structured render failure warning tied to an artifact record."""

    safe_code = code if code in RENDER_WARNING_CODES else "RENDER_EXPORT_FAILED"
    return WarningRecord(
        f"warning-{artifact.id}-{safe_code.lower()}",
        message,
        source="cross_section_renderer",
        code=safe_code,
        related_item_refs=(owner_id,),
        related_artifact_refs=(artifact.id,),
        technical_details=technical_details,
        repair_suggestion="Regenerate the process output artifact.",
    )


def mark_render_artifact_failed(
    artifact: ArtifactRecord,
    warning: WarningRecord,
) -> ArtifactRecord:
    """Return a failed artifact record linked to its render warning."""

    return replace(
        artifact,
        status=ArtifactStatus.FAILED,
        warning_ids=(warning.id,),
        repair=ArtifactRepairMetadata(
            "regenerate_process_output",
            "Regenerate the failed render artifact.",
            last_error=warning.message,
        ),
    )


def _file_metadata(render_result: CrossSectionRenderResult | None) -> ArtifactFileMetadata:
    if render_result is None:
        return ArtifactFileMetadata(content_type="image/svg+xml")
    return ArtifactFileMetadata(
        width_px=render_result.width_px,
        height_px=render_result.height_px,
        content_type="image/png" if render_result.path.endswith(".png") else "image/svg+xml",
    )


def _artifact_extensions(
    scene: CrossSectionSceneModel,
    render_result: CrossSectionRenderResult | None,
) -> dict[str, object]:
    metadata = dict(render_result.render_metadata or {}) if render_result else {}
    metadata.update(
        {
            "render_profile_id": _source_ref(scene, "render_profile_id"),
            "render_mode_id": scene.render_mode_id,
            "theme_id": str(metadata.get("theme_id", "engineering_dark")),
            "background_color": str(metadata.get("background_color", "#0b1120")),
            "compression_metadata": scene.compression_metadata.__dict__,
            "render_warnings": scene.warnings,
            "simplification": _simplification_metadata(scene),
            "label_layout_warnings": tuple(
                item for item in scene.warnings if item.startswith("RENDER_LABEL")
            ),
            "physical_units": scene.physical_units,
            "generator_version": "1",
        }
    )
    return {"cross_section_render": metadata}


def _source_ref(scene: CrossSectionSceneModel, key: str) -> str:
    return str(dict(scene.source_refs or {}).get(key, ""))


def _simplification_metadata(scene: CrossSectionSceneModel) -> tuple[dict[str, object], ...]:
    return tuple(
        dict(item) for item in scene.annotations if item.get("kind") == "render_simplification"
    )
