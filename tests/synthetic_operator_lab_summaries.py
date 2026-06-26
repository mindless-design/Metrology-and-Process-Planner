"""Summary and debug helpers for the synthetic operator lab."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from metrology_process_planner.domains.session import ArtifactRecord, SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.reporting.builder import ReportModelBuilder
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from tests.synthetic_process_lab import write_debug_json


def summarize_session(session: SessionRecord) -> dict[str, Any]:
    """Return compact deterministic summaries for golden comparisons."""

    return {
        "session": {
            "id": session.id,
            "mode": session.mode.value,
            "capture_count": len(session.captures),
            "process_output_count": len(session.process_outputs),
            "report_count": len(session.reports),
            "warning_codes": sorted({warning.code for warning in session.warnings}),
        },
        "solver_outputs": _solver_outputs(session),
        "render_scenes": _render_scenes(session),
        "artifact_registry": _artifact_registry(session),
        "reports": _reports(session),
    }


def report_sections(session: SessionRecord) -> tuple[str, ...]:
    """Return deterministic report section ids for the process review template."""

    document = SessionDocumentBuilder().build(session)
    template = built_in_report_templates()["process_review"]
    report = ReportModelBuilder().build(
        document,
        template,
        requested_sections=("artifact_gallery", "warning_summary", "appendix"),
    )
    return tuple(section.section_id for section in report.sections)


def write_failure_debug(name: str, payload: object) -> Path:
    """Write a debug payload under the existing synthetic debug root."""

    return write_debug_json(f"{name}.operator_lab.json", payload)


def write_gallery_manifest(session: SessionRecord, paths: SessionPaths, name: str) -> Path:
    """Write an optional compact manifest for manual visual review."""

    payload = {
        "session_id": session.id,
        "session_folder": str(paths.folder),
        "visual_artifacts": [
            {
                "id": artifact.id,
                "label": artifact.label,
                "status": artifact.status.value,
                "path": artifact.relative_path,
                "role": artifact.owner.role,
            }
            for artifact in sorted_artifacts(session)
            if "image" in artifact.type or "image" in artifact.owner.role
        ],
    }
    return write_debug_json(f"{name}.gallery_manifest.json", payload)


def sorted_artifacts(session: SessionRecord) -> tuple[ArtifactRecord, ...]:
    """Return artifact records in deterministic id order."""

    return tuple(sorted((session.artifacts or {}).values(), key=lambda item: item.id))


def _solver_outputs(session: SessionRecord) -> list[dict[str, Any]]:
    outputs = []
    for output in sorted(session.process_outputs, key=lambda item: item.id):
        solver = dict(output.extensions or {}).get("solver_result", {})
        frames = solver.get("frames", ()) if isinstance(solver, Mapping) else ()
        outputs.append(
            {
                "id": output.id,
                "status": output.status,
                "type": output.output_type,
                "artifact_roles": sorted(dict(output.artifact_refs or {})),
                "frame_count": len(frames) if isinstance(frames, list) else 0,
                "diagnostics": sorted(dict(output.metadata or {}).get("diagnostic_codes", ())),
            }
        )
    return outputs


def _render_scenes(session: SessionRecord) -> list[dict[str, Any]]:
    scenes = []
    for artifact in sorted_artifacts(session):
        render = dict(dict(artifact.extensions or {}).get("cross_section_render", {}))
        if render:
            scenes.append(_render_scene_summary(artifact, render))
    return scenes


def _render_scene_summary(
    artifact: ArtifactRecord,
    render: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "role": artifact.owner.role,
        "status": artifact.status.value,
        "render_mode_id": render.get("render_mode_id", ""),
        "render_profile_id": render.get("render_profile_id", ""),
        "warnings": sorted(render.get("render_warnings", ())),
    }


def _artifact_registry(session: SessionRecord) -> list[dict[str, Any]]:
    return [
        {
            "id": artifact.id,
            "type": artifact.type,
            "role": artifact.owner.role,
            "status": artifact.status.value,
            "generator": artifact.generator,
            "repair_action": artifact.repair.repair_action,
            "warning_count": len(artifact.warning_ids),
        }
        for artifact in sorted_artifacts(session)
    ]


def _reports(session: SessionRecord) -> list[dict[str, Any]]:
    return [
        {
            "id": report.id,
            "type": report.report_type,
            "status": report.status,
            "artifact_roles": sorted(dict(report.artifact_refs or {})),
            "warning_count": len(report.warning_ids),
        }
        for report in sorted(session.reports, key=lambda item: item.id)
    ]
