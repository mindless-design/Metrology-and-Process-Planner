"""Qt widget fakes for KLayout boundary tests."""

from __future__ import annotations


class FakeWidget:
    """Fake Qt widget that records title, layout, and show calls."""

    def __init__(self) -> None:
        self.title = ""
        self.shown = False
        self._mpp_state = {}
        self.layout = None

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        """Record the requested window title."""

        self.title = title

    def setLayout(self, layout) -> None:  # noqa: N802
        """Record the assigned layout."""

        self.layout = layout

    def show(self) -> None:
        """Record that the window was shown."""

        self.shown = True


class FakeVBoxLayout:
    """Fake Qt layout that records added widgets."""

    def __init__(self) -> None:
        self.widgets = []

    def addWidget(self, widget) -> None:  # noqa: N802
        """Record an added widget."""

        self.widgets.append(widget)


class FakeLabel:
    """Fake Qt label."""

    def __init__(self, text: str) -> None:
        self.text = text


class FakeButton:
    """Fake Qt button."""

    def __init__(self, text: str) -> None:
        self.text = text
