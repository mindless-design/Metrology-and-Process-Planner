import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.geometry import Box, Point
from metrology_process_planner.domains.measurement.records import MeasurementRecord
from metrology_process_planner.domains.session import (
    ArtifactDependencyRef,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
    CaptureGeometry,
    CaptureRecord,
    ModeDefinition,
    ModeRegistry,
    ReportRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    SessionDocumentStore,
    mark_metadata_edit,
)


def _measurement() -> MeasurementRecord:
    return MeasurementRecord(
        "meas-001",
        "Gate CD",
        Point(1, 1),
        Point(3, 1),
        target=2.0,
        lower_spec_limit=1.8,
        upper_spec_limit=2.2,
    )


def _capture() -> CaptureRecord:
    return CaptureRecord(
        "cap-001",
        "Site 7",
        CaptureGeometry.box(Box(0, 0, 5, 5)),
        "2026-06-24T00:00:00Z",
        sequence=7,
        measurements=(_measurement(),),
    )


def _artifacts() -> dict[str, ArtifactRecord]:
    return {
        "site-image": ArtifactRecord(
            "site-image",
            "image",
            "Labeled Site Image",
            "images/site.png",
            ArtifactOwnerRef("capture", "cap-001", "site_image_labeled"),
        ),
        "measurement-annotation": ArtifactRecord(
            "measurement-annotation",
            "image",
            "Measurement Annotation",
            "images/measurement.png",
            ArtifactOwnerRef("measurement", "meas-001", "measurement_annotation_image"),
        ),
        "summary-csv": ArtifactRecord(
            "summary-csv",
            "csv",
            "Capture CSV",
            "exports/session_summary.csv",
            ArtifactOwnerRef("session", "session-001", "csv"),
            dependencies=(ArtifactDependencyRef(kind="capture", id="cap-001"),),
        ),
        "pptx-report": ArtifactRecord(
            "pptx-report",
            "pptx",
            "PowerPoint Report",
            "reports/session_report.pptx",
            ArtifactOwnerRef("report", "report-001", "pptx"),
            dependencies=(ArtifactDependencyRef(kind="capture", id="cap-001"),),
        ),
    }


def _session() -> SessionRecord:
    return SessionRecord(
        "session-001",
        "Editable Session",
        SessionMode.SIMPLE_CAPTURE,
        "2026-06-24T00:00:00Z",
        "2026-06-24T00:00:00Z",
        captures=(_capture(),),
        reports=(
            ReportRecord(
                "report-001",
                "Session Report",
                "pptx",
                artifact_refs={"pptx": "pptx-report"},
            ),
        ),
        artifacts=_artifacts(),
    )

def _recipe_free_registry_for(mode_id: str) -> ModeRegistry:
    return ModeRegistry((ModeDefinition(mode_id, "Recipe Free Override"),))

if __name__ == "__main__":
    unittest.main()


class SessionEditingWorkflowTestsPart3(unittest.TestCase):
    def test_recipe_free_store_save_preserves_hidden_process_artifact_state(self) -> None:
        registry = _recipe_free_registry_for(SessionMode.PROFILOMETRY_PLANNER.value)
        hidden = ArtifactRecord(
            "legacy-process-csv",
            "process_output",
            "Legacy Process Export",
            "process_outputs/legacy.csv",
            ArtifactOwnerRef("process_output", "legacy-stack", "csv"),
            status=ArtifactStatus.PRESENT,
            dependencies=(ArtifactDependencyRef(kind="capture", id="cap-001"),),
        )
        session = replace(
            _session(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            artifacts={**_session().artifacts, hidden.id: hidden},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            _write_session_fixture(paths, session)
            store = SessionDocumentStore(mode_registry=registry)
            document = store.load(paths.session_json)
            edited = mark_metadata_edit(
                document,
                "capture:cap-001",
                "label",
                "Renamed Site",
                registry,
            )

            store.save(edited, paths)
            reloaded = store.load(paths.session_json)

        self.assertEqual("Renamed Site", reloaded.session.captures[0].label)
        self.assertEqual(ArtifactStatus.STALE, reloaded.session.artifacts["site-image"].status)
        self.assertEqual(ArtifactStatus.STALE, reloaded.session.artifacts["summary-csv"].status)
        self.assertEqual(ArtifactStatus.PRESENT, reloaded.session.artifacts[hidden.id].status)
        self.assertNotIn("stale_reason", reloaded.session.artifacts[hidden.id].extensions)


def _write_session_fixture(paths: SessionPaths, session: SessionRecord) -> None:
    paths.ensure_created()
    for folder in ("images", "exports", "reports", "process_outputs"):
        (paths.folder / folder).mkdir(exist_ok=True)
    (paths.folder / "images" / "site.png").write_text("site", encoding="utf-8")
    (paths.folder / "images" / "measurement.png").write_text(
        "measurement",
        encoding="utf-8",
    )
    (paths.folder / "exports" / "session_summary.csv").write_text(
        "csv",
        encoding="utf-8",
    )
    (paths.folder / "reports" / "session_report.pptx").write_text(
        "pptx",
        encoding="utf-8",
    )
    (paths.folder / "process_outputs" / "legacy.csv").write_text(
        "legacy",
        encoding="utf-8",
    )
    paths.session_json.write_text(json.dumps(session.to_dict()), encoding="utf-8")
