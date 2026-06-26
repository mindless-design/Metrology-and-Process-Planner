"""Typed policy blocks for declarative workflow modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModeCapabilities:
    """Compact feature contract for a mode."""

    uses_setup_guide: bool = False
    uses_canvas_objects: bool = True
    supports_measurements: bool = False
    supports_grid_datasets: bool = False
    supports_process_solver: bool = False
    supports_reporting: bool = False
    supports_batch_capture: bool = False
    supports_artifact_regeneration: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ModeCapabilities:
        """Build capabilities from JSON-compatible mode data."""

        defaults = cls()
        values = {
            key: bool(data.get(key, getattr(defaults, key)))
            for key in cls.__dataclass_fields__
        }
        return cls(**values)


@dataclass(frozen=True)
class SetupDefinition:
    """Setup-guide policy for a mode."""

    required: bool = False
    origin_policy: str = "optional"
    can_skip: bool = True
    resume_behavior: str = "resume_incomplete_stage"
    stage_types: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> SetupDefinition:
        """Build setup policy from JSON-compatible mode data."""

        stages = data.get("stages", ())
        return cls(
            required=bool(data.get("required", False)),
            origin_policy=str(data.get("origin_policy", "optional")),
            can_skip=bool(data.get("can_skip", True)),
            resume_behavior=str(data.get("resume_behavior", "resume_incomplete_stage")),
            stage_types=tuple(
                str(item.get("type", ""))
                for item in stages
                if isinstance(item, Mapping)
            ),
        )


@dataclass(frozen=True)
class CaptureSequenceDefinition:
    """Capture workflow policy for a mode."""

    sequence_type: str = "repeat"
    primitive_type: str = "box_capture"
    supported_primitives: tuple[str, ...] = ("site_box",)
    site_role: str = "site"
    inner_feature_type: str = ""
    inner_feature_role: str = ""
    inner_feature_kind: str = ""
    inner_feature_label: str = ""
    child_canvas_object_type: str = ""
    validators: tuple[str, ...] = ()
    review: bool = True
    saved_capture_type: str = ""
    extension_key: str = ""
    feature_id_field: str = ""
    process_output_key: str = ""
    repeat_label_template: str = "Site {sequence:02d}"

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        primitives: tuple[str, ...] = ("site_box",),
    ) -> CaptureSequenceDefinition:
        """Build capture policy from JSON-compatible mode data."""

        primitive = _mapping(data.get("primitive"))
        primitive_type = str(primitive.get("type", data.get("capture_sequence", "box_capture")))
        site = _mapping(primitive.get("site"))
        inner = _mapping(primitive.get("inner_feature"))
        return cls(
            sequence_type=str(data.get("sequence_type", "repeat")),
            primitive_type=primitive_type,
            supported_primitives=primitives,
            site_role=str(site.get("role", primitive.get("role", "site"))),
            inner_feature_type=str(inner.get("type", "")),
            inner_feature_role=str(inner.get("role", "")),
            inner_feature_kind=_inner_kind(inner),
            inner_feature_label=str(inner.get("label", "")),
            child_canvas_object_type=str(inner.get("canvas_object_type", "")),
            validators=_strings(inner.get("validate", ())),
            review=bool(primitive.get("review", True)),
            saved_capture_type=str(data.get("saved_capture_type", "")),
            extension_key=str(data.get("extension_key", "")),
            feature_id_field=str(data.get("feature_id_field", "")),
            process_output_key=str(data.get("process_output_key", "")),
            repeat_label_template=str(data.get("repeat_label_template", "Site {sequence:02d}")),
        )


@dataclass(frozen=True)
class MetadataFieldDefinition:
    """One safe declarative metadata field."""

    id: str
    label: str = ""
    field_type: str = "text"
    required: bool = False
    default: str = ""
    options: tuple[str, ...] = ()

    @classmethod
    def from_value(cls, value: object) -> MetadataFieldDefinition:
        """Build one metadata field definition from mode data."""

        if isinstance(value, Mapping):
            field_id = str(value.get("id", ""))
            return cls(
                field_id,
                str(value.get("label", "")),
                str(value.get("type", "text")),
                bool(value.get("required", False)),
                "" if value.get("default") is None else str(value.get("default", "")),
                _strings(value.get("options", value.get("choices", ()))),
            )
        return cls(str(value))


@dataclass(frozen=True)
class MetadataSchema:
    """Metadata fields and review guidance for a mode."""

    capture_fields: tuple[MetadataFieldDefinition, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> MetadataSchema:
        """Build metadata schema from JSON-compatible mode data."""

        fields = tuple(
            MetadataFieldDefinition.from_value(item)
            for item in data.get("capture_fields", ())
        )
        return cls(fields)

    def field_ids(self) -> tuple[str, ...]:
        """Return declared capture metadata field ids."""

        return tuple(field.id for field in self.capture_fields if field.id)


@dataclass(frozen=True)
class MeasurementPolicy:
    """Measurement workflow policy for a mode."""

    enabled: bool = False
    primitive: str = "line_capture"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> MeasurementPolicy:
        """Build measurement policy from JSON-compatible mode data."""

        geometry = _mapping(data.get("geometry"))
        return cls(bool(data.get("enabled", False)), str(geometry.get("primitive", "line_capture")))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _strings(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return ()


def _inner_kind(inner: Mapping[str, Any]) -> str:
    primitive_type = str(inner.get("type", ""))
    if primitive_type == "line_capture":
        return "line"
    if primitive_type == "point_capture":
        return "point"
    return ""
