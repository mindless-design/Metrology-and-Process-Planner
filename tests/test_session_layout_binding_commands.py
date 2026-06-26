import unittest
from dataclasses import replace
from tempfile import TemporaryDirectory

from metrology_process_planner.app.bootstrap import build_app_services
from metrology_process_planner.app.commands import CommandId
from metrology_process_planner.app.session_layout_adapter import LayoutBindingSelection
from metrology_process_planner.domains.session import (
    ModeDefinition,
    ModeRegistry,
    SessionMode,
    SourceLayoutContext,
    WarningRecord,
)
from metrology_process_planner.workflows.editor import SessionDocumentBuilder
from metrology_process_planner.workflows.overlays import CanvasOverlayManager, OverlayCommand
from tests.editor_render_fixtures import session_without_pending
from tests.session_lifecycle_command_fixtures import document_store, paths_for


class SessionLayoutBindingCommandTests(unittest.TestCase):
    def test_bind_current_layout_updates_source_layout_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = paths_for(temp_dir)
            document_store().save(SessionDocumentBuilder().build(session_without_pending()), paths)
            layout = SourceLayoutContext(
                layout_path="C:/layout/demo.gds",
                layout_name="demo.gds",
                top_cell="TOP",
                layout_fingerprint="abc123",
                klayout_version="0.29.0",
            )
            services = build_app_services(layout_adapter=_FakeLayoutAdapter(layout))
            services.session_editor_controller.open_session_path(paths.session_json)

            result = services.command_router.route(CommandId.BIND_CURRENT_LAYOUT_TO_SESSION)

            document = services.session_editor_controller.current_document
            self.assertEqual("success", result.status)
            self.assertEqual(layout, document.session.source_layout)
            reloaded = document_store().load(paths.session_json)
            self.assertEqual("abc123", reloaded.session.source_layout.layout_fingerprint)

    def test_bind_current_layout_restores_canvas_overlays(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = paths_for(temp_dir)
            document_store().save(SessionDocumentBuilder().build(session_without_pending()), paths)
            backend = _FakeOverlayBackend()
            services = build_app_services(
                layout_adapter=_FakeLayoutAdapter(SourceLayoutContext(layout_path="layout.gds")),
                overlay_manager=CanvasOverlayManager(backend),
            )
            services.session_editor_controller.open_session_path(paths.session_json)

            result = services.command_router.route(CommandId.BIND_CURRENT_LAYOUT_TO_SESSION)

            self.assertEqual("success", result.status)
            self.assertEqual(["restore_object"], [item.kind.value for item in backend.commands])

    def test_bind_current_layout_mismatch_adds_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = paths_for(temp_dir)
            source = replace(
                session_without_pending(),
                source_layout=SourceLayoutContext(
                    layout_path="old.gds",
                    top_cell="OLD_TOP",
                    layout_fingerprint="old-fingerprint",
                ),
            )
            document_store().save(SessionDocumentBuilder().build(source), paths)
            services = build_app_services(
                layout_adapter=_FakeLayoutAdapter(
                    SourceLayoutContext(
                        layout_path="new.gds",
                        top_cell="NEW_TOP",
                        layout_fingerprint="new-fingerprint",
                    )
                )
            )
            services.session_editor_controller.open_session_path(paths.session_json)

            result = services.command_router.route(CommandId.BIND_CURRENT_LAYOUT_TO_SESSION)

            warning_codes = tuple(
                warning.code
                for warning in services.session_editor_controller.current_document.warnings
            )
            self.assertEqual("success", result.status)
            self.assertIn("source-layout-mismatch", result.warning_ids)
            self.assertIn("SOURCE_LAYOUT_MISMATCH", warning_codes)

    def test_cancelled_layout_bind_does_not_mutate_document(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = paths_for(temp_dir)
            document_store().save(SessionDocumentBuilder().build(session_without_pending()), paths)
            services = build_app_services(layout_adapter=_FakeLayoutAdapter())
            services.session_editor_controller.open_session_path(paths.session_json)

            result = services.command_router.route(CommandId.BIND_CURRENT_LAYOUT_TO_SESSION)

            self.assertEqual("cancelled", result.status)
            self.assertEqual(
                SourceLayoutContext(),
                services.session_editor_controller.current_document.session.source_layout,
            )

    def test_bind_current_layout_preserves_loaded_recipe_free_registry(self) -> None:
        registry = ModeRegistry(
            (ModeDefinition(SessionMode.PROFILOMETRY_PLANNER.value, "Recipe Free Override"),)
        )
        with TemporaryDirectory() as temp_dir:
            paths = paths_for(temp_dir)
            source = replace(
                session_without_pending(),
                mode=SessionMode.PROFILOMETRY_PLANNER,
                warnings=(
                    WarningRecord(
                        "process-warning",
                        "Recipe attached but hidden",
                        source="process_context",
                        code="PROCESS_CONTEXT_ATTACHED",
                    ),
                ),
            )
            document_store().save(
                SessionDocumentBuilder(mode_registry=registry).build(source),
                paths,
            )
            services = build_app_services(
                layout_adapter=_FakeLayoutAdapter(SourceLayoutContext(layout_path="layout.gds")),
                mode_registry=registry,
            )
            services.session_editor_controller.open_session_path(paths.session_json)

            result = services.command_router.route(CommandId.BIND_CURRENT_LAYOUT_TO_SESSION)

            document = services.session_editor_controller.current_document
            self.assertEqual("success", result.status)
            self.assertNotIn(
                "process-warning",
                {warning.warning_id for warning in document.warning_view_models},
            )


class _FakeLayoutAdapter:
    def __init__(self, layout: SourceLayoutContext | None = None) -> None:
        self._layout = layout

    def select_current_layout(self) -> LayoutBindingSelection:
        if self._layout is None:
            return LayoutBindingSelection()
        return LayoutBindingSelection.selected(self._layout)


class _FakeOverlayBackend:
    def __init__(self) -> None:
        self.commands: list[OverlayCommand] = []

    def apply(self, command: OverlayCommand) -> None:
        self.commands.append(command)


if __name__ == "__main__":
    unittest.main()
