"""Regenerate synthetic process solver and render golden summaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))


SOLVER_CASES = (
    "simple_stack_recipe",
    "conformal_liner_recipe",
    "tapered_etch_recipe",
    "profilometry_surface_recipe",
    "fib_full_stack_recipe",
)


def main() -> None:
    """Write deterministic solver and render summary snapshots."""

    from tests.test_synthetic_render_regression import RENDER_CASES, _scene_summary
    from tests.test_synthetic_solver_regression import _solver_summary

    root = ROOT / "tests" / "golden"
    solver_root = root / "solver"
    render_root = root / "render"
    solver_root.mkdir(parents=True, exist_ok=True)
    render_root.mkdir(parents=True, exist_ok=True)
    for recipe_id in SOLVER_CASES:
        _write_json(solver_root / f"{recipe_id}.expected.json", _solver_summary(recipe_id))
    for recipe_id, profile_id in RENDER_CASES:
        _write_json(
            render_root / f"{recipe_id}.{profile_id}.expected.json",
            _scene_summary(recipe_id, profile_id),
        )


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
