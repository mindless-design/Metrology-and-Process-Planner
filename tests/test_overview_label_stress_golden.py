import json
import re
import unittest
from pathlib import Path

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.rendering.overview import build_overview_scene
from metrology_process_planner.rendering.overview.models import LabelBox, OverviewDiagramScene
from metrology_process_planner.rendering.overview.renderer import OverviewDiagramRenderer


class OverviewLabelStressGoldenTests(unittest.TestCase):
    def test_dense_real_layout_overview_matches_golden_summary(self) -> None:
        scene = build_overview_scene(_label_stress_session())
        svg = OverviewDiagramRenderer().render_svg(scene)

        self.assertEqual(_golden_label_stress_summary(), _overview_golden_summary(scene, svg))


def _label_stress_session() -> SessionRecord:
    manifest_path = Path(__file__).parent / "fixtures/gds/process_planner_testchip.geometry.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rectangles = tuple(
        rect for rect in manifest["rectangles"] if rect["structure"] == "label_stress_test"
    )
    captures = tuple(_label_stress_capture(index, rect) for index, rect in enumerate(rectangles, 1))
    return SessionRecord(
        "session-label-stress",
        "Label Stress Test",
        SessionMode.SIMPLE_CAPTURE,
        "2026-06-24T00:00:00Z",
        "2026-06-24T00:00:00Z",
        captures=captures,
    )


def _label_stress_capture(index: int, rect: dict[str, object]) -> CaptureRecord:
    geometry = CaptureGeometry.box(
        Box(
            float(rect["x_min"]),
            float(rect["y_min"]),
            float(rect["x_max"]),
            float(rect["y_max"]),
        )
    )
    return CaptureRecord(
        f"label-stress-{index:02d}",
        str(rect["name"]).replace("_", " ").title(),
        geometry,
        "2026-06-24T00:00:00Z",
        sequence=index,
        metadata={"structure": str(rect["structure"]), "layer": str(rect["layer_name"])},
    )


def _overview_golden_summary(scene: OverviewDiagramScene, svg: str) -> dict[str, object]:
    return {
        "scene_id": scene.scene_id,
        "target_count": len(scene.target_shapes),
        "label_count": len(scene.label_boxes),
        "leader_count": len(scene.leader_paths),
        "warnings": list(scene.warnings),
        "placement_metadata": {
            "strategy_used": scene.placement_metadata.strategy_used,
            "labels_requested": scene.placement_metadata.labels_requested,
            "labels_placed": scene.placement_metadata.labels_placed,
            "labels_omitted": scene.placement_metadata.labels_omitted,
            "collisions_resolved": scene.placement_metadata.collisions_resolved,
            "unresolved_collisions": scene.placement_metadata.unresolved_collisions,
            "fallback_steps_used": list(scene.placement_metadata.fallback_steps_used),
        },
        "layout_bounds": scene.layout_bounds.to_dict(),
        "first_label": _label_summary(scene.label_boxes[0]),
        "last_label": _label_summary(scene.label_boxes[-1]),
        "svg": {
            "contains_svg": svg.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<svg '),
            "target_rect_count": len(re.findall(r'<rect [^>]*fill="none" stroke="', svg)),
            "label_box_count": svg.count('rx="4" ry="4"'),
            "leader_count": svg.count("<polyline "),
        },
    }


def _label_summary(label: LabelBox) -> dict[str, object]:
    return {
        "target_id": label.target_id,
        "bounds": label.bounds.to_dict(),
        "text_lines": list(label.text_lines),
    }


def _golden_label_stress_summary() -> dict[str, object]:
    path = Path(__file__).parent / "golden/overview/label_stress_overview.expected.json"
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
