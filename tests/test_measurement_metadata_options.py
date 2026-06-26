import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.measurement.records import (
    EDGE_CONVENTION_OPTIONS,
    MEASUREMENT_TYPE_OPTIONS,
)
from metrology_process_planner.domains.modes.mode_non_process_vocab import (
    CDSEM_FEATURE_TYPES,
)
from metrology_process_planner.domains.session import SessionMode
from metrology_process_planner.persistence.paths import SessionPaths
from metrology_process_planner.workflows.editor import (
    DefaultSessionModeAdapter,
    apply_metadata_edits,
    mark_metadata_edit,
)
from metrology_process_planner.workflows.editor.adapter_mode_fields import mode_metadata_fields
from tests.measurement_child_fixtures import saved_measurement_document


class MeasurementMetadataOptionTests(unittest.TestCase):
    def test_cdsem_mode_declares_measurement_option_sets(self) -> None:
        fields = _mode_fields(SessionMode.CDSEM_MEASUREMENT.value)

        self.assertEqual(CDSEM_FEATURE_TYPES, fields["feature_type"].options)
        self.assertEqual(MEASUREMENT_TYPE_OPTIONS, fields["measurement_type"].options)
        self.assertEqual(EDGE_CONVENTION_OPTIONS, fields["edge_convention"].options)

    def test_measurement_editor_edge_convention_key_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)

        dirty = mark_metadata_edit(
            document,
            "measurement:meas-001",
            "edge_convention",
            "inner_edges",
        )
        applied = apply_metadata_edits(dirty)

        measurement = applied.session.captures[0].measurements[0]
        self.assertEqual("inner_edges", measurement.edge_detection_convention)

    def test_generic_measurement_editor_declares_measurement_option_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = SessionPaths.for_folder(Path(temp_dir))
            paths.ensure_created()
            document = saved_measurement_document(paths)

        fields = _fields_by_key(
            DefaultSessionModeAdapter().metadata_fields(
                document.session,
                document.items_by_id["measurement:meas-001"],
            )
        )

        self.assertEqual(MEASUREMENT_TYPE_OPTIONS, fields["measurement_type"].options)
        self.assertEqual(EDGE_CONVENTION_OPTIONS, fields["edge_convention"].options)
        self.assertIn("lsl", fields)
        self.assertIn("usl", fields)
        self.assertIn("color", fields)
        self.assertNotIn("lower_spec_limit", fields)
        self.assertNotIn("upper_spec_limit", fields)
        self.assertNotIn("annotation_color", fields)


def _mode_fields(mode_id: str):
    return {field.key: field for field in mode_metadata_fields(mode_id, {})}


def _fields_by_key(fields):
    return {field.key: field for field in fields}


if __name__ == "__main__":
    unittest.main()
