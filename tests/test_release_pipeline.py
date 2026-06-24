import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.build_package import build_package, stage_package
from tools.klayout_runner import _existing_path
from tools.package_manifest import iter_release_files
from tools.release_check import PROJECT_ROOT, _run_klayout_lanes


class ReleasePipelineTests(unittest.TestCase):
    def test_release_manifest_excludes_development_files(self) -> None:
        release_paths = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in iter_release_files(PROJECT_ROOT)
        }

        self.assertIn("grain.xml", release_paths)
        self.assertIn("pymacros/metrology_process_planner_bootstrap.py", release_paths)
        self.assertIn("python/metrology_process_planner/__init__.py", release_paths)
        self.assertNotIn("pyproject.toml", release_paths)
        self.assertFalse(any(path.startswith("tests/") for path in release_paths))

    def test_stage_package_creates_klayout_package_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            staged = stage_package(Path(temp_dir) / "package")

            self.assertTrue((staged / "grain.xml").exists())
            self.assertTrue((staged / "pymacros").is_dir())
            self.assertTrue((staged / "python" / "metrology_process_planner").is_dir())

    def test_build_package_creates_zip_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            archive = build_package(Path(temp_dir) / "package.zip")

            self.assertTrue(archive.exists())
            self.assertGreater(archive.stat().st_size, 0)

    def test_klayout_release_lanes_enable_real_tests(self) -> None:
        with mock.patch("tools.release_check._run", return_value=0) as run:
            result = _run_klayout_lanes()

        self.assertEqual(0, result)
        self.assertEqual(2, run.call_count)
        for call in run.call_args_list:
            self.assertEqual(
                {
                    "MPP_RUN_KLAYOUT_TESTS": "1",
                    "MPP_RUN_KLAYOUT_UI_TESTS": "1",
                },
                call.kwargs["env"],
            )

    def test_klayout_discovery_ignores_inaccessible_candidate_paths(self) -> None:
        with mock.patch("pathlib.Path.exists", side_effect=PermissionError("denied")):
            result = _existing_path("C:/inaccessible/klayout_app.exe")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
