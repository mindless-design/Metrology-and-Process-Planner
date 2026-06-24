from metrology_process_planner.domains.session import (
    ArtifactFileMetadata,
    ArtifactOwnerRef,
    ArtifactRecord,
    ArtifactStatus,
)
from metrology_process_planner.domains.session.artifact_ids import artifact_id


def capture_crop_artifact(
    capture_id: str = "cap-001",
    path: str = "images/cap-001.png",
    width_px: int = 800,
    height_px: int = 600,
) -> ArtifactRecord:
    return ArtifactRecord(
        id=artifact_id("capture", capture_id, "crop"),
        type="image",
        label="crop",
        relative_path=path,
        owner=ArtifactOwnerRef("capture", capture_id, "crop"),
        status=ArtifactStatus.PRESENT,
        file=ArtifactFileMetadata(
            width_px=width_px,
            height_px=height_px,
            content_type="image/png",
        ),
    )
