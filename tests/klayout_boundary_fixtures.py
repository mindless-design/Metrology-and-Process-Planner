"""Shared fakes for KLayout boundary tests."""

from __future__ import annotations


class SourceLayoutTrap:
    """Trap object that records accidental source-layout mutation."""

    def __init__(self) -> None:
        self.mutated = False

    def insert_shape(self) -> None:
        """Record mutation if a test accidentally edits source geometry."""

        self.mutated = True


class FakePya:
    """Small fake pya module for active cell-view metadata tests."""

    def __init__(self, layout_path: str, top_cell: str) -> None:
        self.Application = _FakeApplicationFactory(layout_path, top_cell)


class _FakeApplicationFactory:
    """Fake `pya.Application` factory."""

    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._application = _FakeApplication(layout_path, top_cell)

    def instance(self):
        """Return the fake singleton application."""

        return self._application


class _FakeApplication:
    """Fake KLayout application."""

    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._main_window = _FakeMainWindow(layout_path, top_cell)

    def main_window(self):
        """Return the fake main window."""

        return self._main_window

    def version(self) -> str:
        """Return a stable fake KLayout version."""

        return "0.29.fake"


class _FakeMainWindow:
    """Fake KLayout main window."""

    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._view = _FakeView(layout_path, top_cell)

    def current_view(self):
        """Return the fake current view."""

        return self._view


class _FakeView:
    """Fake KLayout view."""

    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._cell_view = _FakeCellView(layout_path, top_cell)

    def active_cellview(self):
        """Return the fake active cell view."""

        return self._cell_view


class _FakeCellView:
    """Fake active cell view."""

    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._layout = _FakeLayout(layout_path)
        self._cell = _FakeCell(top_cell)

    def layout(self):
        """Return the fake layout."""

        return self._layout

    def cell(self):
        """Return the fake top cell."""

        return self._cell


class _FakeLayout:
    """Fake KLayout layout."""

    def __init__(self, layout_path: str) -> None:
        self._layout_path = layout_path

    def filename(self) -> str:
        """Return the fake layout file path."""

        return self._layout_path

    def dbu(self) -> float:
        """Return a stable database unit."""

        return 0.001

    def cells(self) -> int:
        """Return a stable cell count."""

        return 1


class _FakeCell:
    """Fake KLayout cell."""

    def __init__(self, name: str) -> None:
        self._name = name

    def name(self) -> str:
        """Return the fake cell name."""

        return self._name
