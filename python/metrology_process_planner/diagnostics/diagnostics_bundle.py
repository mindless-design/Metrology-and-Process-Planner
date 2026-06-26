"""Debug bundle export for broken sessions."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from metrology_process_planner import __version__
from metrology_process_planner.diagnostics.diagnostics_models import DiagnosticEvent
from metrology_process_planner.diagnostics.diagnostics_seams import (
    check_session_to_editor_seam,
    check_session_to_filesystem_seam,
)
from metrology_process_planner.diagnostics.diagnostics_sinks import DiagnosticSink
from metrology_process_planner.diagnostics.diagnostics_snapshots import (
    snapshot_artifact_manifest,
    snapshot_canvas_objects,
    snapshot_filesystem_artifacts,
    snapshot_session_document,
)
from metrology_process_planner.domains.session import SessionRecord
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.editor.document import SessionDocument


@dataclass(frozen=True)
class DiagnosticsService:
    """Create diagnostic reports and debug bundles."""

    sink: DiagnosticSink

    def export_debug_bundle(
        self,
        session: SessionRecord,
        output_path: Path,
        paths: SessionPaths | None = None,
    ) -> Path:
        """Write a safe-to-share debug bundle folder and return it."""

        bundle = output_path
        bundle.mkdir(parents=True, exist_ok=True)
        session_paths = paths if paths is not None else SessionPaths.for_folder(bundle)
        document = SessionDocumentBuilder().build(session)
        reports = {
            "session_to_editor": check_session_to_editor_seam(document).to_dict(),
            "session_to_filesystem": check_session_to_filesystem_seam(
                session,
                session_paths,
            ).to_dict(),
        }
        _write_json(bundle / "session.json", session.to_dict())
        _copy_if_exists(session_paths.capture_csv, bundle / "captures.csv")
        _write_json(bundle / "artifact_manifest.json", snapshot_artifact_manifest(session))
        _write_json(bundle / "state_snapshots.json", _snapshots(document, session, session_paths))
        _write_json(bundle / "seam_check_report.json", reports)
        (bundle / "seam_check_report.md").write_text(_markdown_report(reports), encoding="utf-8")
        self.sink.export_json(bundle / "diagnostics" / "events.json")
        _write_jsonl(bundle / "diagnostics" / "events.jsonl", self.sink.recent(100_000))
        _write_json(bundle / "bundle_metadata.json", _metadata(session))
        return bundle


def _snapshots(
    document: SessionDocument,
    session: SessionRecord,
    paths: SessionPaths,
) -> dict[str, object]:
    return {
        "session_document": snapshot_session_document(document),
        "canvas_objects": snapshot_canvas_objects(session),
        "artifact_manifest": snapshot_artifact_manifest(session),
        "filesystem_artifacts": snapshot_filesystem_artifacts(paths),
    }


def _metadata(session: SessionRecord) -> dict[str, object]:
    return {
        "plugin_version": __version__,
        "schema_version": session.schema_version,
        "mode_id": session.mode.value,
        "session_id": session.id,
    }


def _markdown_report(reports: dict[str, dict[str, object]]) -> str:
    lines = ["# Seam Check Report", ""]
    for name, report in reports.items():
        status = "OK" if report.get("ok") else "FAILED"
        lines.extend((f"## {name}: {status}", ""))
        for key in ("missing", "extra", "mismatched", "warnings", "suggested_repairs"):
            values = report.get(key)
            if isinstance(values, list) and values:
                lines.append(f"- {key}: " + "; ".join(str(item) for item in values))
        lines.append("")
    return "\n".join(lines)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, events: tuple[DiagnosticEvent, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
