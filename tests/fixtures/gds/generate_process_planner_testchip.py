"""Generate the deterministic Process Planner synthetic GDS testchip."""

from __future__ import annotations

import json
import struct
from collections.abc import Iterable
from pathlib import Path

from process_planner_testchip_data import LAYERS, LayerDef, Rect, rectangles

ROOT = Path(__file__).resolve().parent
GDS_PATH = ROOT / "process_planner_testchip.gds"
MANIFEST_PATH = ROOT / "process_planner_testchip.geometry.json"


def main() -> None:
    """Write the GDS testchip and JSON geometry manifest."""

    rects = rectangles()
    _write_gds(GDS_PATH, rects)
    MANIFEST_PATH.write_text(json.dumps(_manifest(rects), indent=2, sort_keys=True) + "\n")


def _manifest(rects: tuple[Rect, ...]) -> dict[str, object]:
    return {
        "gds": GDS_PATH.name,
        "top_cell": "PROCESS_PLANNER_TESTCHIP",
        "units": "um",
        "database_unit_um": 0.001,
        "layers": [layer.__dict__ for layer in LAYERS],
        "structures": sorted({rect.structure for rect in rects}),
        "rectangles": [rect.__dict__ for rect in rects],
    }


def _write_gds(path: Path, rects: Iterable[Rect]) -> None:
    rect_tuple = tuple(rects)
    structure_names = tuple(sorted({rect.structure for rect in rect_tuple}))
    records = [
        _record(0x00, 0x02, _i2(600)),
        _record(0x01, 0x02, _i2(0) * 12),
        _record(0x02, 0x06, _ascii("MPP_SYNTHETIC")),
        _record(0x03, 0x05, _gds_real(0.001) + _gds_real(1e-9)),
    ]
    for structure_name in structure_names:
        records.extend(
            _cell_records(
                structure_name,
                (rect for rect in rect_tuple if rect.structure == structure_name),
            )
        )
    records.extend(
        [
            _record(0x05, 0x02, _i2(0) * 12),
            _record(0x06, 0x06, _ascii("PROCESS_PLANNER_TESTCHIP")),
        ]
    )
    for structure_name in structure_names:
        records.extend(_sref_records(structure_name))
    records.extend((_record(0x07, 0x00, b""), _record(0x04, 0x00, b"")))
    path.write_bytes(b"".join(records))


def _cell_records(cell_name: str, rects: Iterable[Rect]) -> list[bytes]:
    layer_by_name = {layer.name: layer for layer in LAYERS}
    records = [
        _record(0x05, 0x02, _i2(0) * 12),
        _record(0x06, 0x06, _ascii(cell_name)),
    ]
    for rect in rects:
        records.extend(_boundary_records(rect, layer_by_name[rect.layer_name]))
    records.append(_record(0x07, 0x00, b""))
    return records


def _boundary_records(rect: Rect, layer: LayerDef) -> list[bytes]:
    scale = 1000
    points = (
        (rect.x_min, rect.y_min),
        (rect.x_max, rect.y_min),
        (rect.x_max, rect.y_max),
        (rect.x_min, rect.y_max),
        (rect.x_min, rect.y_min),
    )
    xy = b"".join(_i4(round(x * scale)) + _i4(round(y * scale)) for x, y in points)
    return [
        _record(0x08, 0x00, b""),
        _record(0x0D, 0x02, _i2(layer.layer)),
        _record(0x0E, 0x02, _i2(layer.datatype)),
        _record(0x10, 0x03, xy),
        _record(0x11, 0x00, b""),
    ]


def _sref_records(cell_name: str) -> list[bytes]:
    return [
        _record(0x0A, 0x00, b""),
        _record(0x12, 0x06, _ascii(cell_name)),
        _record(0x10, 0x03, _i4(0) + _i4(0)),
        _record(0x11, 0x00, b""),
    ]


def _record(record_type: int, data_type: int, data: bytes) -> bytes:
    return _i2(len(data) + 4) + bytes((record_type, data_type)) + data


def _ascii(value: str) -> bytes:
    data = value.encode("ascii")
    return data + (b"\0" if len(data) % 2 else b"")


def _i2(value: int) -> bytes:
    return struct.pack(">h", value)


def _i4(value: int) -> bytes:
    return struct.pack(">i", value)


def _gds_real(value: float) -> bytes:
    if value == 0:
        return b"\0" * 8
    sign = 0x80 if value < 0 else 0
    mantissa = abs(value)
    exponent = 64
    while mantissa < 1 / 16:
        mantissa *= 16
        exponent -= 1
    while mantissa >= 1:
        mantissa /= 16
        exponent += 1
    integer = int(mantissa * (1 << 56))
    return bytes((sign | exponent,)) + integer.to_bytes(7, "big")


if __name__ == "__main__":
    main()
