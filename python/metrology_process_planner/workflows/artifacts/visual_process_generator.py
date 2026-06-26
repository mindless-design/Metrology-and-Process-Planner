"""Concrete visual process artifact generator handlers."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.process import ProcessRecipe
from metrology_process_planner.domains.session import (
    ArtifactRecord,
    ArtifactRepairMetadata,
    CaptureRecord,
    ProcessOutputRecord,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths, artifact_path_to_disk
from metrology_process_planner.rendering.cross_section import (
    CrossSectionOutputSpec,
    CrossSectionRenderResult,
    CrossSectionSceneModel,
    SvgCrossSectionRenderer,
    build_cross_section_scene,
    build_render_artifact_record,
    resolve_render_profile,
)
from metrology_process_planner.solver.solver_outputs import SolverResult
from metrology_process_planner.workflows.artifacts.generators import ArtifactGenerationResult
from metrology_process_planner.workflows.process_regeneration import solve_capture_process_output
from metrology_process_planner.workflows.process_regeneration_records import ready_output


def regenerate_visual_process_artifact(
    session: SessionRecord,
    artifact: ArtifactRecord,
    paths: SessionPaths,
) -> ArtifactGenerationResult:
    """Regenerate a process-owned visual artifact through solver/render contracts."""

    capture = _capture_by_id(session, artifact.owner.owner_id)
    if capture is None:
        raise RuntimeError(f"Capture {artifact.owner.owner_id} was not found.")
    recipe = _load_recipe(session.process_context.recipe_path)
    solver_result = solve_capture_process_output(capture, recipe)
    role = _visual_role(artifact)
    resolution = resolve_render_profile(role, _requested_profile_id(artifact))
    profile = resolution.profile
    relative_path = _relative_svg_path(artifact)
    destination = artifact_path_to_disk(paths.folder, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    scene = build_cross_section_scene(
        solver_result,
        profile,
        scene_id=f"{capture.id}-{role}",
        title=artifact.label or profile.display_name,
    )
    scene = _with_profile_resolution_warnings(scene, resolution.warnings)
    rendered = SvgCrossSectionRenderer().render(
        scene,
        CrossSectionOutputSpec(
            width_px=profile.output_size[0],
            height_px=profile.output_size[1],
            theme_id=profile.theme_id,
            output_path=str(destination),
            artifact_id=artifact.id,
        ),
    )
    repaired = _repairable_record(artifact, role, relative_path, scene, rendered)
    return ArtifactGenerationResult(
        repaired,
        _with_ready_process_output(session, capture, repaired, solver_result),
    )


def _capture_by_id(session: SessionRecord, capture_id: str) -> CaptureRecord | None:
    return next((item for item in session.captures if item.id == capture_id), None)


def _load_recipe(recipe_path: str) -> ProcessRecipe:
    if not recipe_path:
        raise RuntimeError("No process recipe is attached.")
    try:
        return ProcessRecipe.from_dict(json.loads(Path(recipe_path).read_text(encoding="utf-8")))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Process recipe could not be loaded: {exc}") from exc


def _visual_role(artifact: ArtifactRecord) -> str:
    role = artifact.owner.role or artifact.type
    if not role:
        raise RuntimeError(f"Artifact {artifact.id} is not a visual process artifact.")
    return role


def _requested_profile_id(artifact: ArtifactRecord) -> str:
    metadata = dict(artifact.extensions or {})
    render = dict(metadata.get("cross_section_render", {}))
    return str(render.get("render_profile_id", ""))


def _with_profile_resolution_warnings(
    scene: CrossSectionSceneModel,
    warnings: tuple[str, ...],
) -> CrossSectionSceneModel:
    if not warnings:
        return scene
    return replace(scene, warnings=tuple(dict.fromkeys(scene.warnings + warnings)))


def _relative_svg_path(artifact: ArtifactRecord) -> str:
    path = artifact.relative_path
    if path and Path(path).suffix.lower() == ".svg":
        return path
    return f"images/{artifact.id}.svg"


def _repairable_record(
    artifact: ArtifactRecord,
    role: str,
    relative_path: str,
    scene: CrossSectionSceneModel,
    rendered: CrossSectionRenderResult,
) -> ArtifactRecord:
    record = build_render_artifact_record(
        artifact.owner.owner_type,
        artifact.owner.owner_id,
        role,
        role,
        relative_path,
        scene,
        rendered,
    )
    return replace(
        record,
        repair=ArtifactRepairMetadata(
            "regenerate_process_output",
            "Regenerate visual process artifact.",
            regenerable=True,
            requires_recipe=True,
            requires_solver=True,
        ),
    )


def _with_ready_process_output(
    session: SessionRecord,
    capture: CaptureRecord,
    artifact: ArtifactRecord,
    solver_result: SolverResult,
) -> SessionRecord:
    outputs = list(session.process_outputs)
    output = _ready_output_with_artifact(ready_output(capture, solver_result), artifact)
    replaced = [output if item.id == output.id else item for item in outputs]
    if all(item.id != output.id for item in outputs):
        replaced.append(output)
    artifacts = {**dict(session.artifacts or {}), artifact.id: artifact}
    return replace(session, process_outputs=tuple(replaced), artifacts=artifacts)


def _ready_output_with_artifact(
    output: ProcessOutputRecord,
    artifact: ArtifactRecord,
) -> ProcessOutputRecord:
    refs = {**dict(output.artifact_refs or {}), artifact.owner.role: artifact.id}
    metadata = dict(output.metadata or {})
    profile_id = _artifact_render_profile_id(artifact)
    if profile_id:
        metadata["render_profile_id"] = profile_id
    return replace(output, artifact_refs=refs, metadata=metadata)


def _artifact_render_profile_id(artifact: ArtifactRecord) -> str:
    render = dict(dict(artifact.extensions or {}).get("cross_section_render", {}))
    return str(render.get("render_profile_id", ""))
