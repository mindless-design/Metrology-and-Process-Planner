"""Extra deterministic rectangle builders for the synthetic testchip."""

from __future__ import annotations

from process_planner_testchip_data import Rect


def label_stress_rectangles() -> tuple[Rect, ...]:
    """Return dense label-stress geometry."""

    return tuple(
        Rect(
            "label_stress_test",
            "LABEL_STRESS_TEST",
            f"narrow_feature_{idx}",
            80 + idx * 0.7,
            60,
            80.35 + idx * 0.7,
            75,
        )
        for idx in range(18)
    )


def grid_rectangles() -> tuple[Rect, ...]:
    """Return site-grid geometry."""

    rects = [
        Rect("grid_capture_test", "ALIGN", "anchor_a", 0, 90, 2, 92),
        Rect("grid_capture_test", "ALIGN", "anchor_b", 30, 90, 32, 92),
    ]
    rects.extend(
        Rect(
            "grid_capture_test",
            "GRID",
            f"site_r{row}_c{col}",
            5 + col * 8,
            96 + row * 8,
            7 + col * 8,
            98 + row * 8,
        )
        for row in range(3)
        for col in range(4)
    )
    return tuple(rects)
