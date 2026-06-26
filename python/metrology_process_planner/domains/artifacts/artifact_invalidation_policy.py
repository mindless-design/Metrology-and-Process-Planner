"""Role and type sets used by artifact invalidation rules."""

from __future__ import annotations

CAPTURE_LABEL_ROLES = {
    "crop",
    "site_image",
    "site_image_labeled",
    "labeled_site_image",
    "site_overview",
    "line_annotation",
    "line_annotation_png",
    "line_annotation_svg",
    "point_annotation",
    "point_annotation_png",
    "point_annotation_svg",
    "layout_annotation",
    "layout_annotation_png",
    "layout_annotation_svg",
}

MEASUREMENT_METADATA_ROLES = {
    "measurement_annotation",
    "measurement_annotation_image",
    "measurement_annotation_png",
    "measurement_annotation_svg",
    "measurement_detail",
    "measurement_context_image",
}

EXPORT_RELEVANT_TYPES = {
    "csv",
    "capture_csv",
    "session_csv",
    "session_summary_csv",
    "report",
    "pptx",
    "powerpoint",
    "pdf",
}

EXPORT_RELEVANT_ROLES = {
    "csv",
    "capture_csv",
    "session_summary_csv",
    "report",
    "powerpoint",
    "pptx",
    "pdf",
}
