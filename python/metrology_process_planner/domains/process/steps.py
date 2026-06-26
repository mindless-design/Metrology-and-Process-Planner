"""Process step models and thickness/window validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from metrology_process_planner.domains.process.materials import LayerReference
from metrology_process_planner.domains.process.step_values import (
    bounded_value_warnings,
    optional_float,
    optional_str,
)
from metrology_process_planner.solver.geometry_models import MaskInterval
from metrology_process_planner.solver.solver_profiles import (
    ConformalProfile,
    EtchProfile,
    PlanarizationProfile,
)


class MaskPolarity(str, Enum):
    """How a layout mask should be interpreted by a process step."""

    DIRECT = "direct"
    INVERTED = "inverted"


class ProcessStepKind(str, Enum):
    """Supported simplified fabrication operations."""

    SUBSTRATE = "substrate"
    BLANKET_DEPOSITION = "blanket_deposition"
    PATTERNED_DEPOSITION = "patterned_deposition"
    CONFORMAL_COATING = "conformal_coating"
    CONFORMAL_DEPOSITION = "conformal_deposition"
    DIRECTIONAL_ETCH = "directional_etch"
    ISOTROPIC_ETCH = "isotropic_etch"
    TAPERED_ETCH = "tapered_etch"
    PLANARIZATION = "planarization"
    CMP_PLANARIZATION = "cmp_planarization"
    ANNOTATION_ONLY = "annotation_only"


class RenderProfileRef(str):
    """Identifier for a render profile used by a process-aware output."""


@dataclass(frozen=True)
class ThicknessSpec:
    """Nominal and optional bounded thickness for a process step."""

    target: float
    lower: Optional[float] = None
    upper: Optional[float] = None
    unit: str = "um"

    def validate(self) -> tuple[str, ...]:
        """Return warnings for inconsistent thickness limits."""

        warnings: list[str] = []
        if self.target < 0:
            warnings.append("Thickness target must be non-negative.")
        warnings.extend(bounded_value_warnings(self.lower, self.target, self.upper, "Thickness"))
        return tuple(warnings)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the thickness spec to JSON-compatible data."""

        return {
            "target": self.target,
            "lower": self.lower,
            "upper": self.upper,
            "unit": self.unit,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ThicknessSpec:
        """Build a thickness spec from saved JSON-compatible data."""

        return cls(
            target=float(data["target"]),
            lower=optional_float(data.get("lower")),
            upper=optional_float(data.get("upper")),
            unit=str(data.get("unit", "um")),
        )


@dataclass(frozen=True)
class ProcessWindow:
    """Lower, target, and upper value for process planning."""

    name: str
    lower: float
    target: float
    upper: float
    unit: str = "um"

    def validate(self) -> tuple[str, ...]:
        """Return warnings when a process window is not ordered."""

        if self.lower <= self.target <= self.upper:
            return ()
        return ("Process window must satisfy lower <= target <= upper.",)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the process window to JSON-compatible data."""

        return {
            "name": self.name,
            "lower": self.lower,
            "target": self.target,
            "upper": self.upper,
            "unit": self.unit,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessWindow:
        """Build a process window from saved JSON-compatible data."""

        return cls(
            name=str(data["name"]),
            lower=float(data["lower"]),
            target=float(data["target"]),
            upper=float(data["upper"]),
            unit=str(data.get("unit", "um")),
        )


@dataclass(frozen=True)
class ProcessStep:
    """One simplified process operation in an ordered recipe."""

    id: str
    kind: ProcessStepKind
    material_id: Optional[str] = None
    thickness: Optional[ThicknessSpec] = None
    layer: Optional[LayerReference] = None
    mask_polarity: MaskPolarity = MaskPolarity.DIRECT
    target_material_ids: tuple[str, ...] = ()
    stop_material_ids: tuple[str, ...] = ()
    mask_intervals: tuple[MaskInterval, ...] = ()
    conformal_profile: Optional[ConformalProfile] = None
    etch_profile: Optional[EtchProfile] = None
    planarization_profile: Optional[PlanarizationProfile] = None
    parameters: Optional[Mapping[str, Any]] = None
    notes: str = ""
    name: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.parameters is None:
            object.__setattr__(self, "parameters", {})

    def to_dict(self) -> dict[str, Any]:
        """Serialize the process step to JSON-compatible data."""

        return {
            "id": self.id,
            "kind": self.kind.value,
            "name": self.name,
            "enabled": self.enabled,
            "material_id": self.material_id,
            "thickness": self.thickness.to_dict() if self.thickness is not None else None,
            "layer": self.layer.to_dict() if self.layer is not None else None,
            "mask_polarity": self.mask_polarity.value,
            "target_material_ids": list(self.target_material_ids),
            "stop_material_ids": list(self.stop_material_ids),
            "mask_intervals": [
                {"x_min": item.x_min, "x_max": item.x_max} for item in self.mask_intervals
            ],
            "parameters": dict(self.parameters or {}),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProcessStep:
        """Build a process step from saved JSON-compatible data."""

        layer_data = data.get("layer")
        polarity = data.get("mask_polarity", MaskPolarity.DIRECT.value)
        parameters = dict(data.get("parameters", {}))
        name = str(data.get("name", parameters.get("name", "")))
        enabled = bool(data.get("enabled", parameters.get("enabled", True)))
        return cls(
            id=str(data["id"]),
            kind=ProcessStepKind(str(data["kind"])),
            name=name,
            enabled=enabled,
            material_id=optional_str(data.get("material_id")),
            thickness=(
                ThicknessSpec.from_dict(data["thickness"])
                if data.get("thickness") is not None
                else None
            ),
            layer=LayerReference.from_dict(layer_data) if layer_data is not None else None,
            mask_polarity=MaskPolarity(str(polarity)),
            target_material_ids=tuple(str(item) for item in data.get("target_material_ids", ())),
            stop_material_ids=tuple(str(item) for item in data.get("stop_material_ids", ())),
            mask_intervals=tuple(
                MaskInterval(float(item["x_min"]), float(item["x_max"]))
                for item in data.get("mask_intervals", ())
            ),
            parameters=parameters,
            notes=str(data.get("notes", "")),
        )
