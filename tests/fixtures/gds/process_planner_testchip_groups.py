"""Private geometry groups for the synthetic Process Planner testchip."""

from __future__ import annotations

try:
    from tests.fixtures.gds.process_planner_testchip_data import Rect
except ModuleNotFoundError:
    from process_planner_testchip_data import Rect


def line_space() -> tuple[Rect, ...]:
    """Return line-space challenge geometry."""

    rects = [
        Rect("simple_line_space", "POLY", "isolated_1um", 0, 0, 1, 12),
        Rect("simple_line_space", "POLY", "isolated_3um", 4, 0, 7, 12),
    ]
    rects.extend(
        Rect(
            "simple_line_space",
            "METAL1",
            f"dense_line_{idx}",
            12 + idx * 1.2,
            0,
            12.5 + idx * 1.2,
            12,
        )
        for idx in range(8)
    )
    return tuple(rects)


def trench_via() -> tuple[Rect, ...]:
    """Return trench and via challenge geometry."""

    return (
        Rect("trench_via_etch", "TRENCH", "wide_trench", 40, 0, 52, 4),
        Rect("trench_via_etch", "TRENCH", "narrow_trench", 40, 7, 50, 8),
        Rect("trench_via_etch", "CONTACT", "square_via_1", 55, 0, 57, 2),
        Rect("trench_via_etch", "VIA", "square_via_2", 60, 0, 62, 2),
    )


def undercut() -> tuple[Rect, ...]:
    """Return isotropic undercut challenge geometry."""

    return (
        Rect("isotropic_undercut", "ACTIVE", "sacrificial_strip", 80, 0, 105, 5),
        Rect("isotropic_undercut", "TRENCH", "release_opening", 88, 0, 92, 5),
        Rect("isotropic_undercut", "METAL1", "narrow_bridge", 96, 1.8, 102, 3.2),
    )


def liner() -> tuple[Rect, ...]:
    """Return conformal liner challenge geometry."""

    return (
        Rect("conformal_liner_challenge", "LINER_TEST", "narrow_gap", 0, 30, 1, 45),
        Rect("conformal_liner_challenge", "LINER_TEST", "wide_gap", 4, 30, 12, 45),
        Rect("conformal_liner_challenge", "ACTIVE", "step_left", 16, 30, 22, 38),
        Rect("conformal_liner_challenge", "ACTIVE", "step_right", 22, 30, 28, 45),
    )


def cmp() -> tuple[Rect, ...]:
    """Return CMP density challenge geometry."""

    rects = [Rect("cmp_planarization_density", "CMP_DENSITY", "sparse_block", 40, 30, 55, 45)]
    rects.extend(
        Rect(
            "cmp_planarization_density",
            "CMP_DENSITY",
            f"dense_{row}_{col}",
            60 + col * 1.5,
            30 + row * 1.5,
            61 + col * 1.5,
            31 + row * 1.5,
        )
        for row in range(5)
        for col in range(5)
    )
    return tuple(rects)


def profilometry() -> tuple[Rect, ...]:
    """Return profilometry surface challenge geometry."""

    return (
        Rect("profilometry_surface_test", "PROFILE_TEST", "surface_step_low", 80, 30, 94, 40),
        Rect("profilometry_surface_test", "PROFILE_TEST", "surface_step_high", 94, 30, 108, 45),
        Rect("profilometry_surface_test", "METAL1", "buried_change", 85, 32, 102, 34),
    )


def fib() -> tuple[Rect, ...]:
    """Return FIB full-stack challenge geometry."""

    return (
        Rect("fib_full_stack_test", "FIB_CUT_TEST", "cut_line_context", 0, 60, 30, 62),
        Rect("fib_full_stack_test", "METAL1", "thin_top_metal", 6, 58, 18, 64),
        Rect("fib_full_stack_test", "LINER_TEST", "thin_liner_marker", 20, 58, 22, 64),
    )


def point_stack() -> tuple[Rect, ...]:
    """Return point-stack challenge geometry."""

    return (
        Rect("point_stack_ellipsometry", "POINT_STACK_TEST", "field_point", 40, 60, 43, 63),
        Rect("point_stack_ellipsometry", "METAL1", "metal_point", 46, 60, 52, 66),
        Rect("point_stack_ellipsometry", "METAL2", "overlap_point", 49, 63, 55, 69),
    )


def label_stress() -> tuple[Rect, ...]:
    """Return dense label stress-test geometry."""

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


def grid() -> tuple[Rect, ...]:
    """Return grid capture challenge geometry."""

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
