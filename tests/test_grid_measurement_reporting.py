import unittest
from dataclasses import replace

from metrology_process_planner.domains.session import (
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactRepairMetadata,
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    ReportingPolicy,
    SessionMode,
    WarningRecord,
    built_in_mode_registry,
)
from metrology_process_planner.reporting import ReportModelBuilder
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from metrology_process_planner.workflows.grid_measurement import create_grid_dataset
from tests.test_grid_measurement_workflow import _session

if __name__ == "__main__":
    unittest.main()


class GridMeasurementReportingTests(unittest.TestCase):
    def test_grid_mode_declares_recipe_free_grid_report_section(self) -> None:
        definition = built_in_mode_registry().definition(SessionMode.GRID_MEASUREMENT.value)

        self.assertIn("grid_dataset", definition.reporting.sections)
        self.assertEqual("forbidden", definition.process.recipe_policy)
        self.assertEqual("none", definition.process.solver_operation)

    def test_grid_report_includes_dataset_summary_without_process_context(self) -> None:
        session = create_grid_dataset(_session(), "cap-a", "cap-b", 2, 3, "Gate grid")
        document = SessionDocumentBuilder().build(session)
        template = built_in_report_templates()["capture_catalog"]

        report = ReportModelBuilder().build(document, template)

        self.assertEqual(1, report.session_summary["grid_datasets"])
        self.assertEqual({}, report.process_context_summary)
        self.assertNotIn("process_context", {section.section_id for section in report.sections})
        grid_section = next(
            section for section in report.sections if section.section_id == "grid_dataset"
        )
        row = grid_section.tables[0].rows[0]
        self.assertEqual("grid-001", row["dataset_id"])
        self.assertEqual("Gate grid", row["label"])
        self.assertEqual(2, row["rows"])
        self.assertEqual(3, row["columns"])
        self.assertEqual(6, row["planned_sites"])
        self.assertEqual("grid-001:site-001", row["first_site"])
        self.assertEqual("grid-001:site-006", row["last_site"])
        self.assertEqual("cap-a, cap-b", row["anchors"])
        self.assertEqual("placeholder", row["overview_status"])
        self.assertEqual(1, row["warnings"])

    def test_grid_report_hides_legacy_process_overview_artifact_for_recipe_free_override(
        self,
    ) -> None:
        registry = ModeRegistry(
            (
                ModeDefinition(
                    SessionMode.PROFILOMETRY_PLANNER.value,
                    "Recipe Free Override",
                    reporting=ReportingPolicy(True, ("grid_dataset",)),
                ),
            )
        )
        session = _grid_session_with_hidden_process_overview()
        document = SessionDocumentBuilder(registry).build(session)
        template = built_in_report_templates()["capture_catalog"]

        report = ReportModelBuilder(mode_registry=registry).build(document, template)

        grid_section = next(
            section for section in report.sections if section.section_id == "grid_dataset"
        )
        row = grid_section.tables[0].rows[0]
        self.assertEqual("", row["overview_status"])
        self.assertEqual(0, row["warnings"])
        grid_summary = report.appendix_data["grid_datasets"][0]
        self.assertEqual("", grid_summary["overview_artifact_id"])
        self.assertEqual("", grid_summary["overview_status"])
        self.assertEqual(0, grid_summary["warnings"])
        self.assertEqual((), report.warnings)
        self.assertEqual((), report.artifacts)


def _grid_session_with_hidden_process_overview():
    source = create_grid_dataset(_session(), "cap-a", "cap-b", 1, 1, "Gate grid")
    hidden_process = _hidden_process_grid_overview()
    dataset = replace(
        source.grid_datasets[0],
        artifact_refs={"grid_overview": hidden_process.id},
        warning_ids=("hidden-process-warning",),
    )
    return replace(
        source,
        mode=SessionMode.PROFILOMETRY_PLANNER,
        grid_datasets=(dataset,),
        artifacts={hidden_process.id: hidden_process},
        warnings=_hidden_grid_warnings(hidden_process.id),
    )


def _hidden_process_grid_overview() -> ArtifactRecord:
    return ArtifactRecord(
        "legacy-process-grid-overview",
        "process_output",
        "Legacy Grid Stack",
        "process_outputs/grid-stack.png",
        ArtifactOwnerRef("grid_dataset", "grid-001", "stack_image"),
        status=ArtifactStatus.MISSING,
        repair=ArtifactRepairMetadata(
            repair_action="regenerate_process_output",
            requires_recipe=True,
            requires_solver=True,
        ),
    )


def _hidden_grid_warnings(artifact_id: str) -> tuple[WarningRecord, ...]:
    return (
        WarningRecord(
            "hidden-process-warning",
            "Recipe-backed grid overview is unavailable.",
            source="process_output",
            code="PROCESS_OUTPUT_STALE",
            related_artifact_refs=(artifact_id,),
        ),
    )
