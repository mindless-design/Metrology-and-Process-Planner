import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.domains.modes.mode_non_process_vocab import (
    CAD_REVIEW_CATEGORIES,
    CAD_REVIEW_SEVERITIES,
)
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    SessionDocumentBuilder,
)
from metrology_process_planner.workflows.editor.adapter_mode_fields import mode_metadata_fields
from tests.editor_render_fixtures import session
from tests.measurement_child_fixtures import saved_measurement_document


class NonProcessMetadataFieldTests(unittest.TestCase):
    def test_review_and_cdsem_metadata_have_clear_recipe_free_defaults(self) -> None:
        cad_fields = _mode_fields(SessionMode.CAD_REVIEW.value)
        cdsem_fields = _mode_fields(SessionMode.CDSEM_CAPTURE.value)

        self.assertEqual("Review Category", cad_fields["review_category"].label)
        self.assertEqual("layout_issue", cad_fields["review_category"].value)
        self.assertEqual(CAD_REVIEW_CATEGORIES, cad_fields["review_category"].options)
        self.assertEqual("medium", cad_fields["severity"].value)
        self.assertEqual(CAD_REVIEW_SEVERITIES, cad_fields["severity"].options)
        self.assertEqual("Owner / Assignee", cad_fields["owner"].label)
        self.assertTrue(cdsem_fields["feature_type"].required)
        self.assertEqual("line", cdsem_fields["feature_type"].value)
        self.assertEqual("Measurement Type", cdsem_fields["measurement_type"].label)
        self.assertEqual("cd", cdsem_fields["measurement_type"].value)
        self.assertEqual("outer_edges", cdsem_fields["edge_convention"].value)

    def test_measurement_editor_exposes_generic_measurement_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)

        fields = DefaultSessionModeAdapter().metadata_fields(
            document.session,
            document.items_by_id["measurement:meas-001"],
        )

        self.assertEqual(_required_measurement_fields(), {field.key for field in fields})

    def test_cdsem_capture_metadata_includes_label_length_guidance(self) -> None:
        for mode in (SessionMode.CDSEM_MEASUREMENT, SessionMode.CDSEM_PLANNING):
            with self.subTest(mode=mode.value):
                source = replace(session(), mode=mode)
                document = SessionDocumentBuilder().build(source)
                adapter = DefaultSessionModeAdapter()

                saved_fields = _fields_by_key(
                    adapter.metadata_fields(source, document.items_by_id["capture:cap-001"])
                )
                pending_fields = _fields_by_key(
                    adapter.metadata_fields(source, document.items_by_id["pending:pending-001"])
                )

                self.assertIn("32 characters", saved_fields["label_guidance"].value)
                self.assertTrue(saved_fields["label_guidance"].read_only)
                self.assertIn("32 characters", pending_fields["label_guidance"].value)

    def test_cdsem_capture_metadata_requires_feature_type_with_default(self) -> None:
        for mode in (SessionMode.CDSEM_MEASUREMENT, SessionMode.CDSEM_PLANNING):
            with self.subTest(mode=mode.value):
                source = replace(session(), mode=mode)
                document = SessionDocumentBuilder().build(source)
                adapter = DefaultSessionModeAdapter()

                saved_fields = _fields_by_key(
                    adapter.metadata_fields(source, document.items_by_id["capture:cap-001"])
                )
                pending_fields = _fields_by_key(
                    adapter.metadata_fields(source, document.items_by_id["pending:pending-001"])
                )

                self.assertTrue(saved_fields["feature_type"].required)
                self.assertEqual("line", saved_fields["feature_type"].value)
                self.assertTrue(pending_fields["feature_type"].required)
                self.assertEqual("line", pending_fields["feature_type"].value)

    def test_simple_capture_metadata_does_not_show_cdsem_label_guidance(self) -> None:
        source = session()
        document = SessionDocumentBuilder().build(source)

        fields = DefaultSessionModeAdapter().metadata_fields(
            source,
            document.items_by_id["capture:cap-001"],
        )

        self.assertNotIn("label_guidance", {field.key for field in fields})

    def test_simple_capture_exposes_optional_capture_type_metadata(self) -> None:
        source = session()
        document = SessionDocumentBuilder().build(source)
        adapter = DefaultSessionModeAdapter()

        saved_fields = _fields_by_key(
            adapter.metadata_fields(source, document.items_by_id["capture:cap-001"])
        )
        pending_fields = _fields_by_key(
            adapter.metadata_fields(source, document.items_by_id["pending:pending-001"])
        )

        self.assertEqual("Capture Role", saved_fields["capture_role"].label)
        self.assertEqual("site", saved_fields["capture_role"].value)
        self.assertEqual("Capture Type", saved_fields["capture_type"].label)
        self.assertEqual("layout_region", saved_fields["capture_type"].value)
        self.assertEqual("site", pending_fields["capture_role"].value)
        self.assertEqual("Capture Type", pending_fields["capture_type"].label)

def _mode_fields(mode_id: str):
    return {field.key: field for field in mode_metadata_fields(mode_id, {})}


def _fields_by_key(fields):
    return {field.key: field for field in fields}


def _required_measurement_fields() -> set[str]:
    return {
        "label",
        "measurement_type",
        "target",
        "lsl",
        "usl",
        "notes",
        "edge_convention",
        "color",
        "line_weight",
    }


if __name__ == "__main__":
    unittest.main()
