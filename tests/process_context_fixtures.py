import json
from pathlib import Path

from metrology_process_planner.domains.geometry import Box
from metrology_process_planner.domains.session import (
    CaptureGeometry,
    CaptureRecord,
    SessionMode,
    SessionRecord,
)
from metrology_process_planner.workflows.editor import DefaultSessionModeAdapter


def recipe_path(folder: Path) -> Path:
    path = folder / "recipe.json"
    path.write_text(json.dumps(recipe_payload()), encoding="utf-8")
    return path


def recipe_payload() -> dict[str, object]:
    return {
        "id": "recipe_gate_stack",
        "name": "Gate Stack",
        "version": "1.2.3",
        "materials": [
            {"id": "si", "name": "Si", "color": "#999999"},
            {"id": "oxide", "name": "Oxide", "color": "#66ccff"},
        ],
        "steps": [
            {
                "id": "substrate",
                "kind": "substrate",
                "material_id": "si",
                "thickness": {"target": 1.0},
            },
            {
                "id": "deposit_oxide",
                "kind": "blanket_deposition",
                "material_id": "oxide",
                "thickness": {"target": 0.2},
            },
        ],
    }


def capture_session() -> SessionRecord:
    base = session()
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=base.mode,
        created_at=base.created_at,
        updated_at=base.updated_at,
        captures=(
            CaptureRecord(
                "cap-001",
                "Profile Site 01",
                CaptureGeometry.box(Box(0, 0, 10, 10)),
                base.created_at,
                type="site_plus_line",
            ),
        ),
    )


def custom_process_capture_session() -> SessionRecord:
    base = session()
    capture = CaptureRecord(
        "cap-001",
        "FIB Site 01",
        CaptureGeometry.box(Box(0, 0, 10, 10)),
        base.created_at,
        type="fib_site_line",
        extensions={
            "fib_process": {
                "fib_cut_feature_id": "feat-001",
                "process_context_ref": "process_context.active",
                "solver_request": {
                    "operation": "full_stack_compressed",
                    "process_window_variant": "target",
                    "render_profile": "fib_cross_section",
                },
                "solver_result_id": None,
            }
        },
    )
    return replace_session(base, capture)


def session() -> SessionRecord:
    return SessionRecord(
        id="session-001",
        name="Demo",
        mode=SessionMode.SIMPLE_CAPTURE,
        created_at="2026-06-24T00:00:00Z",
        updated_at="2026-06-24T00:00:00Z",
    )


def replace_session(base: SessionRecord, capture: CaptureRecord) -> SessionRecord:
    return SessionRecord(
        id=base.id,
        name=base.name,
        mode=base.mode,
        created_at=base.created_at,
        updated_at=base.updated_at,
        captures=(capture,),
    )


def dashboard_field(document, key: str) -> str:
    fields = DefaultSessionModeAdapter().metadata_fields(
        document.session,
        document.items_by_id["dashboard"],
    )
    return next(field.value for field in fields if field.key == key)
