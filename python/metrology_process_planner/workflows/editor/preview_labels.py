"""Shared user-facing labels for editor artifact previews."""

from __future__ import annotations


def artifact_preview_label(role: str, artifact_type: str = "") -> str:
    """Return the operator-facing preview label for an artifact role."""

    if role == "report_output":
        return _report_output_label(artifact_type)
    labels = {
        "site_image": "Raw Site Image",
        "crop": "Raw Site Image",
        "site_image_labeled": "Labeled Site Image",
        "site_overview_image": "Site Overview",
        "line_annotation_image": "Annotated Line/Point",
        "point_annotation_image": "Annotated Line/Point",
        "measurement_annotation_image": "Measurement Detail",
        "setup_reference_image": "Setup Reference Image",
        "origin_reference_image": "Origin Reference Image",
        "origin_point_image": "Origin Point Image",
        "optical_alignment_image": "Optical Alignment Image",
        "sem_alignment_image": "SEM Alignment Image",
        "grid_overview": "Grid Overview",
        "grid_overview_image": "Grid Overview",
        "csv_export": "CSV Export",
        "report": "Report Output",
        "report_document": "Report Output",
        "report_output": "Report Output",
        "profile_image": "Profile / Cross Section",
        "cross_section_image": "Profile / Cross Section",
        "stack_image": "Stack / Full Stack",
        "full_stack_compressed_image": "Stack / Full Stack",
    }
    return labels.get(role, role.replace("_", " ").title())


def _report_output_label(artifact_type: str) -> str:
    labels = {
        "powerpoint_deck": "PowerPoint Deck",
        "powerpoint_export": "PowerPoint Deck",
        "pdf_report": "PDF Report",
        "csv_export": "Report CSV Export",
        "image_bundle": "Report Image Bundle",
        "report_manifest": "Report Manifest",
    }
    return labels.get(artifact_type, "Report Output")
