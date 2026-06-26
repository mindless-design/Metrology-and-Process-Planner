import csv
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from metrology_process_planner.app.diagnostics_summary import diagnostics_summary_rows
from metrology_process_planner.app.window_registry import WindowRegistry
from metrology_process_planner.domains.process import ThicknessSpec
from metrology_process_planner.domains.session import (
    DisplayUnitPreferences,
    built_in_mode_registry,
    display_unit_preferences_from_session,
    format_length,
    session_extensions_with_display_units,
)
from metrology_process_planner.persistence.csv_export import CaptureCsvExporter
from metrology_process_planner.rendering.cross_section import (
    RenderIntent,
    build_cross_section_scene,
    built_in_render_profile,
)
from metrology_process_planner.reporting.builder import ReportModelBuilder
from metrology_process_planner.reporting.formatting import table_caption
from metrology_process_planner.reporting.templates import built_in_report_templates
from metrology_process_planner.ui.recipe_editor.summaries import thickness_summary
from metrology_process_planner.workflows.editor.builder import SessionDocumentBuilder
from tests.cross_section_rendering_fixtures import MATERIALS, simple_stack_result
from tests.test_canonical_session_json import _session


class DisplayUnitPreferenceTests(unittest.TestCase):
    def test_auto_unit_selection_prefers_nm_for_thin_films_and_um_for_larger_values(self) -> None:
        self.assertEqual("80 nm", format_length(0.08, "um", "auto"))
        self.assertEqual("1.5 um", format_length(1500, "nm", "auto"))
        self.assertEqual("2 mm", format_length(2_000_000, "nm", "auto"))

    def test_session_extensions_round_trip_without_rewriting_canonical_values(self) -> None:
        session = _session()
        preferences = DisplayUnitPreferences(
            film_thickness="nm",
            layout_geometry="um",
            cross_section_axes="um",
            reports="um",
            diagnostics="um",
        )
        updated = replace(
            session,
            extensions=session_extensions_with_display_units(session, preferences),
        )

        loaded = type(session).from_dict(updated.to_dict())

        self.assertEqual(preferences, display_unit_preferences_from_session(loaded))
        self.assertEqual(5, loaded.captures[0].geometry.bounds.width)

    def test_cross_section_labels_axes_and_scale_bar_use_preferred_units(self) -> None:
        profile = built_in_render_profile("physical_cross_section")
        intent = RenderIntent.from_profile(profile, display_unit_preference="um")

        scene = build_cross_section_scene(
            simple_stack_result(),
            profile,
            intent,
            materials=MATERIALS,
        )

        self.assertEqual("um", scene.physical_units)
        self.assertEqual("um", scene.coordinate_frame["canonical_units"])
        self.assertTrue(any("um" in label.text for label in scene.labels))
        self.assertEqual({"um"}, {axis["units"] for axis in scene.axes})
        self.assertEqual("um", scene.scale_bars[0]["units"])

    def test_recipe_thickness_summary_uses_preferred_film_unit(self) -> None:
        summary = thickness_summary(
            _step_with_thickness(),
            DisplayUnitPreferences(film_thickness="nm"),
        )

        self.assertEqual("80 nm target", summary)

    def test_report_table_and_caption_use_selected_units(self) -> None:
        session = _session_with_preferences(DisplayUnitPreferences(reports="um"))
        document = SessionDocumentBuilder().build(session)

        report = ReportModelBuilder().build(
            document,
            built_in_report_templates()["measurement_catalog"],
        )
        measurement = report.measurements[0]
        table = next(
            item
            for section in report.sections
            for item in section.tables
            if item.table_id == "measurements"
        )

        self.assertEqual("um", measurement.display_unit)
        self.assertEqual("2 um", measurement.measured_length_display)
        self.assertIn("Length (um)", dict(table.columns).values())
        self.assertIn("Units: um", table_caption(table))

    def test_capture_csv_headers_and_rows_use_selected_layout_units(self) -> None:
        session = _session_with_preferences(DisplayUnitPreferences(layout_geometry="um"))
        capture = session.captures[0]
        geometry = replace(capture.geometry, metadata={"units": "nm"})
        session = replace(session, captures=(replace(capture, geometry=geometry),))

        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "captures.csv"
            CaptureCsvExporter().export(session, destination)
            with destination.open(encoding="utf-8") as handle:
                rows = list(csv.reader(handle))

        header = rows[0]
        data = dict(zip(header, rows[1], strict=True))
        self.assertIn("left (um)", header)
        self.assertEqual("um", data["units"])
        self.assertEqual("0.005", data["width (um)"])

    def test_diagnostics_show_display_unit_preference(self) -> None:
        session = _session_with_preferences(DisplayUnitPreferences(layout_geometry="um"))

        rows = dict(
            diagnostics_summary_rows(
                session,
                (),
                built_in_mode_registry(),
                WindowRegistry(),
            )
        )

        self.assertIn("layout_geometry=um", rows["Display Units"])


def _session_with_preferences(preferences: DisplayUnitPreferences):
    session = _session()
    return replace(
        session,
        extensions=session_extensions_with_display_units(session, preferences),
    )


def _step_with_thickness():
    from metrology_process_planner.domains.process import ProcessStep, ProcessStepKind

    return ProcessStep(
        "step-001",
        ProcessStepKind.BLANKET_DEPOSITION,
        material_id="oxide",
        thickness=ThicknessSpec(target=0.08),
    )


if __name__ == "__main__":
    unittest.main()
