"""Fake KLayout host objects for boundary tests."""


class SourceLayoutTrap:
    def __init__(self) -> None:
        self.mutated = False

    def insert_shape(self) -> None:
        self.mutated = True


class FakePya:
    def __init__(self, layout_path: str, top_cell: str) -> None:
        self.Application = FakeApplicationFactory(layout_path, top_cell)


class FakeApplicationFactory:
    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._application = FakeApplication(layout_path, top_cell)

    def instance(self):
        return self._application


class FakeApplication:
    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._main_window = FakeMainWindow(layout_path, top_cell)

    def main_window(self):
        return self._main_window

    def version(self) -> str:
        return "0.29.fake"


class FakeMainWindow:
    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._view = FakeView(layout_path, top_cell)

    def current_view(self):
        return self._view


class FakeView:
    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._cell_view = FakeCellView(layout_path, top_cell)

    def active_cellview(self):
        return self._cell_view


class FakeCellView:
    def __init__(self, layout_path: str, top_cell: str) -> None:
        self._layout = FakeLayout(layout_path)
        self._cell = FakeCell(top_cell)

    def layout(self):
        return self._layout

    def cell(self):
        return self._cell


class FakeLayout:
    def __init__(self, layout_path: str) -> None:
        self._layout_path = layout_path

    def filename(self) -> str:
        return self._layout_path

    def dbu(self) -> float:
        return 0.001

    def cells(self) -> int:
        return 1


class FakeCell:
    def __init__(self, name: str) -> None:
        self._name = name

    def name(self) -> str:
        return self._name
