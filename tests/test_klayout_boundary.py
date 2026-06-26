import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.klayout_boundary_fixtures import FakePya, SourceLayoutTrap
from tests.klayout_widget_fixtures import FakeButton, FakeLabel, FakeVBoxLayout, FakeWidget


class KLayoutBoundaryTests(unittest.TestCase):
    def test_klayout_plugin_module_imports_without_pya(self) -> None:
        from metrology_process_planner.infrastructure.klayout import plugin

        self.assertTrue(hasattr(plugin, "register_plugin"))

    def test_klayout_overlay_backend_does_not_mutate_source_layout(self) -> None:
        from metrology_process_planner.infrastructure.klayout.overlays import KLayoutOverlayBackend
        from metrology_process_planner.workflows import OverlayCommand, OverlayCommandKind

        source_layout = SourceLayoutTrap()
        backend = KLayoutOverlayBackend(
            marker_factory=lambda command: ("marker", command.object_id)
        )

        backend.apply(OverlayCommand(OverlayCommandKind.RESTORE_OBJECT, "canvas-001"))

        self.assertFalse(source_layout.mutated)
        self.assertEqual(1, len(backend.commands))

    def test_klayout_session_layout_adapter_reads_active_cellview_metadata(self) -> None:
        from metrology_process_planner.infrastructure.klayout.session_layout_adapter import (
            KLayoutSessionLayoutAdapter,
        )

        with TemporaryDirectory() as temp_dir:
            layout_path = Path(temp_dir) / "demo.gds"
            layout_path.write_bytes(b"gds")
            pya = FakePya(str(layout_path), "TOP")

            selection = KLayoutSessionLayoutAdapter(pya).select_current_layout()

        self.assertEqual("selected", selection.status)
        self.assertEqual(str(layout_path), selection.source_layout.layout_path)
        self.assertEqual("demo.gds", selection.source_layout.layout_name)
        self.assertEqual("TOP", selection.source_layout.top_cell)
        self.assertEqual("0.29.fake", selection.source_layout.klayout_version)
        self.assertIn("TOP", selection.source_layout.layout_fingerprint)

    def test_klayout_session_editor_shell_renders_document_regions(self) -> None:
        from metrology_process_planner.infrastructure.klayout.session_editor_shell import (
            KLayoutSessionEditorWidgetFactory,
        )
        from metrology_process_planner.ui.session_editor import (
            SessionEditorCallbacks,
            SessionEditorShell,
        )
        from metrology_process_planner.workflows.editor import (
            DefaultSessionModeAdapter,
            SessionDocumentBuilder,
        )
        from tests.editor_render_fixtures import session_without_pending

        selected: list[str] = []
        pya = FakePya("layout.gds", "TOP")
        pya.QWidget = FakeWidget
        pya.QVBoxLayout = FakeVBoxLayout
        pya.QLabel = FakeLabel
        pya.QPushButton = FakeButton
        window = SessionEditorShell(KLayoutSessionEditorWidgetFactory(pya)).open(
            SessionDocumentBuilder().build(session_without_pending()),
            DefaultSessionModeAdapter(),
            SessionEditorCallbacks(selected.append, lambda _action: None),
        )

        window._mpp_state["on_select"]("dashboard")

        self.assertTrue(window.shown)
        self.assertTrue(window.layout.widgets)
        self.assertEqual("Session Editor - Demo", window.title)
        self.assertIn(("Session", "Demo"), window._mpp_state["header"])
        self.assertIn("header", window._mpp_state["qt_regions"])
        self.assertIn("primary_actions", window._mpp_state["qt_regions"])
        self.assertIn("Session | Demo", window._mpp_state["qt_region_labels"]["header"])
        self.assertTrue(window._mpp_state["navigator"])
        self.assertTrue(window._mpp_state["preview"])
        self.assertTrue(window._mpp_state["fields"])
        controls = {
            control["key"]: control
            for control in window._mpp_state["metadata_controls"]
        }
        self.assertEqual("text", controls["session_name"]["control_type"])
        self.assertEqual("label", controls["mode"]["control_type"])
        self.assertEqual("Ready; selected Demo", window._mpp_state["status"])
        self.assertEqual(["dashboard"], selected)


if __name__ == "__main__":
    unittest.main()
