import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.persistence.paths import (
    artifact_path_to_disk,
    normalize_artifact_path,
)


class PathPolicyTests(unittest.TestCase):
    def test_normalizes_portable_artifact_path(self) -> None:
        self.assertEqual("images/site-001.png", normalize_artifact_path("images\\site-001.png"))

    def test_rejects_absolute_paths(self) -> None:
        with self.assertRaises(ValueError):
            normalize_artifact_path("C:/Users/example/site.png")

    def test_rejects_parent_traversal(self) -> None:
        with self.assertRaises(ValueError):
            normalize_artifact_path("../site.png")

    def test_artifact_path_resolves_inside_session_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = artifact_path_to_disk(Path(temp_dir), "images/site-001.png")

        self.assertTrue(str(destination).endswith(str(Path("images") / "site-001.png")))


if __name__ == "__main__":
    unittest.main()

