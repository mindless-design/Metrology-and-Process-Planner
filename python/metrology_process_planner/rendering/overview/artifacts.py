"""Artifact and warning records for overview diagram generation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    SessionRecord,
    WarningRecord,
)
from metrology_process_planner.rendering.overview.models import OverviewDiagramScene
from metrology_process_planner.rendering.overview.scene_io import scene_to_dict

GENERATOR_ID = "overview_diagram_renderer"


def overview_artifact_record(
    session: SessionRecord,
    role: str,
    relative_path: str,
    scene: OverviewDiagramScene,
    status: ArtifactStatus = ArtifactStatus.PRESENT,
) -> ArtifactRecord:
    """Create a central artifact record for a generated overview diagram."""

    artifact_id = f"artifact-{session.id}-{role}"
    return ArtifactRecord(
        id=artifact_id,
        type=_artifact_type(role),
        label=role.replace("_", " ").title(),
        relative_path=relative_path,
        owner=ArtifactOwnerRef("session", session.id, role),
        status=status,
        generator=GENERATOR_ID,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_artifact",
            repair_suggestion="Regenerate the overview diagram.",
            regenerable=True,
        ),
        file=ArtifactFileMetadata(
            width_px=scene.canvas_size[0],
            height_px=scene.canvas_size[1],
            content_type="image/svg+xml",
        ),
        warning_ids=tuple(f"warning-{artifact_id}-{code.lower()}" for code in scene.warnings),
        extensions={
            "diagram_scene_id": scene.scene_id,
            "label_layout_metadata": scene.placement_metadata.__dict__,
            "report_summary": _report_summary(role, scene),
            "overview_scene": scene_to_dict(scene),
        },
    )


def overview_warnings(
    artifact: ArtifactRecord,
    scene: OverviewDiagramScene,
) -> tuple[WarningRecord, ...]:
    """Return structured warnings produced by overview generation."""

    return tuple(_warning_for_code(artifact, code) for code in scene.warnings)


def failed_overview_artifact(
    session: SessionRecord,
    role: str,
    message: str,
) -> tuple[ArtifactRecord, WarningRecord]:
    """Create failed artifact and warning records for renderer failures."""

    scene = OverviewDiagramScene(
        f"scene-{session.id}-{role}-failed",
        role.replace("_", " ").title(),
        "",
        (640, 480),
        Box(0, 0, 640, 480),
        (),
        (),
        (),
        warnings=("OVERVIEW_RENDER_FAILED",),
    )
    artifact = overview_artifact_record(session, role, "", scene, ArtifactStatus.FAILED)
    warning = _warning_for_code(artifact, "OVERVIEW_RENDER_FAILED", message)
    return replace(artifact, warning_ids=(warning.id,)), warning


def write_overview_artifact(
    session: SessionRecord,
    role: str,
    svg_text: str,
    scene: OverviewDiagramScene,
    output_folder: Path,
) -> ArtifactRecord:
    """Write SVG text and return its central artifact record."""

    relative_path = f"artifacts/overviews/{role}.svg"
    destination = output_folder / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg_text, encoding="utf-8")
    return overview_artifact_record(session, role, relative_path, scene)


def _artifact_type(role: str) -> str:
    mapping = {
        "session_overview": "session_overview_image",
        "metrology_overview": "metrology_overview_image",
        "grid_overview": "grid_overview_image",
        "cad_review_overview": "cad_review_overview_image",
        "process_planning_overview": "process_planning_overview_image",
    }
    return mapping.get(role, "overview_image")


def _report_summary(role: str, scene: OverviewDiagramScene) -> dict[str, object]:
    metadata = scene.placement_metadata
    return {
        "role": role,
        "title": scene.title,
        "labels_requested": metadata.labels_requested,
        "labels_placed": metadata.labels_placed,
        "labels_omitted": metadata.labels_omitted,
        "unresolved_collisions": metadata.unresolved_collisions,
        "fallback_steps_used": list(metadata.fallback_steps_used),
        "warnings": list(scene.warnings),
        "source_items": len(scene.target_shapes),
        "leader_count": len(scene.leader_paths),
    }


def _warning_for_code(
    artifact: ArtifactRecord,
    code: str,
    message: str = "",
) -> WarningRecord:
    return WarningRecord(
        id=f"warning-{artifact.id}-{code.lower()}",
        code=code,
        source="overview_diagram",
        severity="warning",
        message=message or _message_for_code(code),
        related_item_refs=(artifact.owner.owner_id,),
        related_artifact_refs=(artifact.id,),
        artifact_path=artifact.relative_path,
        repair_suggestion="Regenerate the overview diagram.",
    )


def _message_for_code(code: str) -> str:
    messages = {
        "LABEL_LAYOUT_COLLISION_UNRESOLVED": "Overview labels still have unresolved collisions.",
        "LABELS_OMITTED_DUE_TO_SPACE": "Some low-priority overview labels were omitted.",
        "OVERVIEW_RENDER_FAILED": "Overview diagram rendering failed.",
    }
    return messages.get(code, code.replace("_", " ").title())
