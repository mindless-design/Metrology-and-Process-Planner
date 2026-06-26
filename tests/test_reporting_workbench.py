import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.reporting_workbench import ReportingWorkbenchController
from metrology_process_planner.domains.session import (
    ArtifactStatus,
    ModeDefinition,
    ModeRegistry,
    ProcessContext,
    SessionMode,
    WarningRecord,
)
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from tests.editor_render_fixtures import session_without_pending
from tests.reporting_workbench_fixtures import document as base_document
from tests.reporting_workbench_fixtures import document_with_artifact


class ReportingWorkbenchTests(unittest.TestCase):
    def test_session_editor_build_report_opens_modeless_workbench(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.session_editor_controller.open_document(base_document(), paths)

            routed = services.command_router.route(CommandId.OPEN_REPORTING_WORKBENCH)

            self.assertEqual("success", routed.status)
            window = services.reporting_workbench_controller.current_window
            assert window is not None
            self.assertTrue(window["shown"])
            self.assertIn("Report Workbench", window["title"])
            model = window["model"]
            self.assertEqual("capture_catalog", model.selected_template_id)
            self.assertIn(("dark", "Dark"), model.themes)

    def test_workbench_exports_powerpoint_with_missing_image_placeholder(self) -> None:
        services = build_app_services()
        document = document_with_artifact(ArtifactStatus.MISSING)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.reporting_workbench_controller.open_document(document, paths)

            result = services.reporting_workbench_controller.dispatch("export_pptx")

            self.assertEqual("success", result.status)
            names = zipfile.ZipFile(result.output_path).namelist()
            self.assertIn("ppt/slides/slide4.xml", names)
            model = services.reporting_workbench_controller.current_window["model"]
            self.assertIn(("Output", result.output_path), model.result_fields)
            self.assertTrue(services.session_editor_controller.current_document.session.reports)
            action_ids = {action.action_id for action in model.actions}
            self.assertIn("open_report", action_ids)
            self.assertIn("regenerate_report", action_ids)

            open_result = services.reporting_workbench_controller.dispatch("open_report")
            self.assertEqual(result.output_path, open_result.output_path)

    def test_workbench_recommends_export_with_placeholders_when_ready_with_warnings(self) -> None:
        services = build_app_services()
        document = document_with_artifact(ArtifactStatus.MISSING)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.reporting_workbench_controller.open_document(document, paths)

            model = services.reporting_workbench_controller.current_window["model"]
            action = next(
                item for item in model.actions if item.action_id == model.primary_action_id
            )

            self.assertEqual("export_pptx", model.primary_action_id)
            self.assertEqual("Export with Placeholders", action.label)
            self.assertIn(("Placeholdered", "missing-image"), model.inspector)

    def test_workbench_template_and_section_selection_refresh_preview(self) -> None:
        services = build_app_services()
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            services.reporting_workbench_controller.open_document(base_document(), paths)

            services.reporting_workbench_controller.select_template("capture_catalog")
            services.reporting_workbench_controller.select_section("artifact_gallery")

            window = services.reporting_workbench_controller.current_window
            assert window is not None
            model = window["model"]
            self.assertEqual("capture_catalog", model.selected_template_id)
            self.assertEqual("artifact_gallery", model.preview.selected_section_id)

    def test_replace_after_export_preserves_loaded_recipe_free_registry(self) -> None:
        registry = ModeRegistry(
            (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
        )
        session = replace(
            session_without_pending(),
            mode=SessionMode.PROFILOMETRY_PLANNER,
            process_context=ProcessContext(recipe_reference="legacy-recipe.json"),
            warnings=(
                WarningRecord(
                    "process-warning",
                    "Recipe attached but hidden",
                    source="process_context",
                    code="PROCESS_CONTEXT_ATTACHED",
                ),
            ),
        )
        document = SessionDocumentBuilder(mode_registry=registry).build(session)
        controller = ReportingWorkbenchController(mode_registry=registry)

        with tempfile.TemporaryDirectory() as temp_dir:
            controller.open_document(document, SessionPaths.for_folder(Path(temp_dir)))
            controller.replace_after_export(session)

        assert controller.current_document is not None
        self.assertEqual((), controller.current_document.warning_view_models)
