import tempfile
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.infrastructure.klayout.layout_crop_exporter import (
    KLayoutLayoutCropExporter,
)


class KLayoutLayoutCropExporterTests(unittest.TestCase):
    def test_exporter_uses_active_view_export_image_boundary(self) -> None:
        pya = _FakePya()
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "crop.png"

            metadata = KLayoutLayoutCropExporter(pya).export_image(Box(0, 0, 2, 1), destination)

        self.assertEqual("image/png", metadata.content_type)
        self.assertEqual((0, 0, 2, 1), pya.view.bounds)
        self.assertTrue(pya.view.wrote)


class _FakePya:
    def __init__(self) -> None:
        self.view = _FakeView()
        self.Application = _FakeApplication(self.view)


class _FakeApplication:
    def __init__(self, view) -> None:
        self._view = view

    def instance(self):
        return self

    def main_window(self):
        return _FakeMainWindow(self._view)


class _FakeMainWindow:
    def __init__(self, view) -> None:
        self._view = view

    def current_view(self):
        return self._view


class _FakeView:
    def __init__(self) -> None:
        self.bounds = None
        self.wrote = False

    def export_image(self, bounds, destination):
        self.bounds = (bounds.left, bounds.bottom, bounds.right, bounds.top)
        destination.write_text("png", encoding="utf-8")
        self.wrote = True


if __name__ == "__main__":
    unittest.main()
