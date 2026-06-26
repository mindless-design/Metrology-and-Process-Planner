import unittest

from tools.klayout_point_probe_scripts import ellipsometry_point_capture_adapter_script
from tools.klayout_probe_scripts import (
    line_capture_adapter_script,
    profilometry_line_capture_adapter_script,
)
from tools.klayout_runner import integration_tests_enabled, run_klayout_python_probe
from tools.klayout_standalone_capture_probe_scripts import (
    standalone_line_capture_adapter_script,
    standalone_point_capture_adapter_script,
)

_KLAYOUT_SKIP_REASON = "Set MPP_RUN_KLAYOUT_TESTS=1 to run real KLayout integration tests."


@unittest.skipUnless(integration_tests_enabled(), _KLAYOUT_SKIP_REASON)
class KLayoutIntegrationTests(unittest.TestCase):
    def test_klayout_imports_plugin_package(self) -> None:
        result = run_klayout_python_probe(
            "import metrology_process_planner\n"
            "print('MPP_VERSION=' + metrology_process_planner.__version__)\n"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("MPP_VERSION=0.1.0", result.stdout)

    def test_klayout_imports_pya_and_adapter_boundary(self) -> None:
        result = run_klayout_python_probe(
            "import pya\n"
            "from metrology_process_planner.infrastructure.klayout import plugin\n"
            "print('PYA_OK=' + str(hasattr(pya, 'Application')))\n"
            "print('PLUGIN_OK=' + str(hasattr(plugin, 'register_plugin')))\n"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("PYA_OK=True", result.stdout)
        self.assertIn("PLUGIN_OK=True", result.stdout)

    def test_klayout_registers_plugin_with_fake_ui(self) -> None:
        result = run_klayout_python_probe(
            "from metrology_process_planner.infrastructure.klayout.plugin import register_plugin\n"
            "class FakeAction:\n"
            "    def __init__(self):\n"
            "        self.title = ''\n"
            "    def on_triggered(self, callback):\n"
            "        self.callback = callback\n"
            "class FakeMenu:\n"
            "    def __init__(self):\n"
            "        self.menus = []\n"
            "        self.items = []\n"
            "    def is_valid(self, name):\n"
            "        return name in self.menus\n"
            "    def insert_menu(self, anchor, name, title):\n"
            "        self.menus.append(name)\n"
            "    def insert_item(self, anchor, name, action):\n"
            "        self.items.append((anchor, name, action.title))\n"
            "class FakeWindow:\n"
            "    def __init__(self):\n"
            "        self.fake_menu = FakeMenu()\n"
            "    def menu(self):\n"
            "        return self.fake_menu\n"
            "class FakeApplication:\n"
            "    def __init__(self):\n"
            "        self.window = FakeWindow()\n"
            "    def main_window(self):\n"
            "        return self.window\n"
            "class FakePya:\n"
            "    Action = FakeAction\n"
            "    class Application:\n"
            "        @staticmethod\n"
            "        def instance():\n"
            "            return fake_application\n"
            "fake_application = FakeApplication()\n"
            "registration = register_plugin(pya_module=FakePya())\n"
            "print('MENU=' + registration.menu_name)\n"
            "print('MENU_PATH=' + registration.menu_path)\n"
            "print('COUNT=' + str(registration.command_count))\n"
            "print('ITEMS=' + str(len(fake_application.window.fake_menu.items)))\n"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("MENU=metrology_process_planner", result.stdout)
        self.assertIn("MENU_PATH=tools_menu.metrology_process_planner", result.stdout)
        lines = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        self.assertEqual(lines["COUNT"], lines["ITEMS"])
        self.assertGreater(int(lines["COUNT"]), 0)

    def test_klayout_qt_svg_rasterizer_writes_png(self) -> None:
        result = run_klayout_python_probe(
            "from pathlib import Path\n"
            "import tempfile\n"
            "from metrology_process_planner.infrastructure.klayout.qt_rasterizer import "
            "QtSvgRasterizer\n"
            "svg = '<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"8\" height=\"8\">'\n"
            "svg += '<rect x=\"0\" y=\"0\" width=\"8\" height=\"8\" fill=\"#00aaee\" /></svg>'\n"
            "with tempfile.TemporaryDirectory() as temp_dir:\n"
            "    destination = Path(temp_dir) / 'out.png'\n"
            "    QtSvgRasterizer().rasterize_svg(svg, destination, 8, 8)\n"
            "    print('PNG_EXISTS=' + str(destination.exists()))\n"
            "    print('PNG_SIZE=' + str(destination.stat().st_size > 0))\n"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("PNG_EXISTS=True", result.stdout)
        self.assertIn("PNG_SIZE=True", result.stdout)

    def test_klayout_resolves_session_editor_command(self) -> None:
        result = run_klayout_python_probe(
            "from metrology_process_planner.app.bootstrap import build_app_services\n"
            "from metrology_process_planner.app.commands import CommandId\n"
            "services = build_app_services()\n"
            "services.commands.dispatch(CommandId.OPEN_SESSION_EDITOR)\n"
            "print('EDITOR_CONTROLLER=' + str(hasattr(services, 'session_editor_controller')))\n"
            "print('EDITOR_CURRENT=' + str(services.session_editor_controller.current_document))\n"
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("EDITOR_CONTROLLER=True", result.stdout)
        self.assertIn("EDITOR_CURRENT=None", result.stdout)

    def test_klayout_line_capture_adapter_does_not_mutate_layout(self) -> None:
        result = run_klayout_python_probe(line_capture_adapter_script())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("LINE_IGNORED=False", result.stdout)
        self.assertIn("LINE_RELEASED=True", result.stdout)
        self.assertIn("MEASUREMENT_ID=meas-001", result.stdout)
        self.assertIn("LAYOUT_UNCHANGED=True", result.stdout)
        self.assertIn("OVERLAY_CANVAS=True", result.stdout)

    def test_klayout_profilometry_line_capture_adapter_does_not_mutate_layout(self) -> None:
        result = run_klayout_python_probe(profilometry_line_capture_adapter_script())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("PROFILE_LINE_RELEASED=True", result.stdout)
        self.assertIn("FEATURE_ROLE=profilometry_line", result.stdout)
        self.assertIn("CHILD_TYPE=profilometry_line", result.stdout)
        self.assertIn("LAYOUT_UNCHANGED=True", result.stdout)
        self.assertIn("OVERLAY_CHILD=True", result.stdout)

    def test_klayout_ellipsometry_point_capture_adapter_does_not_mutate_layout(self) -> None:
        result = run_klayout_python_probe(ellipsometry_point_capture_adapter_script())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("POINT_IGNORED=False", result.stdout)
        self.assertIn("POINT_CLICKED=True", result.stdout)
        self.assertIn("FEATURE_ROLE=ellipsometry_point", result.stdout)
        self.assertIn("CHILD_TYPE=ellipsometry_point", result.stdout)
        self.assertIn("LAYOUT_UNCHANGED=True", result.stdout)
        self.assertIn("OVERLAY_CHILD=True", result.stdout)

@unittest.skipUnless(integration_tests_enabled(), _KLAYOUT_SKIP_REASON)
class KLayoutStandaloneIntegrationTests(unittest.TestCase):
    def test_klayout_standalone_point_capture_adapter_does_not_mutate_layout(self) -> None:
        result = run_klayout_python_probe(standalone_point_capture_adapter_script())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("POINT_IGNORED=False", result.stdout)
        self.assertIn("POINT_CLICKED=True", result.stdout)
        self.assertIn("PENDING_KIND=point", result.stdout)
        self.assertIn("POINT_X=2", result.stdout)
        self.assertIn("POINT_Y=2", result.stdout)
        self.assertIn("LAYOUT_UNCHANGED=True", result.stdout)
        self.assertIn("OVERLAY_POINT=True", result.stdout)

    def test_klayout_standalone_line_capture_adapter_does_not_mutate_layout(self) -> None:
        result = run_klayout_python_probe(standalone_line_capture_adapter_script())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("LINE_IGNORED=False", result.stdout)
        self.assertIn("LINE_RELEASED=True", result.stdout)
        self.assertIn("PENDING_KIND=line", result.stdout)
        self.assertIn("LINE_START_X=1", result.stdout)
        self.assertIn("LINE_END_X=4", result.stdout)
        self.assertIn("LAYOUT_UNCHANGED=True", result.stdout)
        self.assertIn("OVERLAY_LINE=True", result.stdout)
