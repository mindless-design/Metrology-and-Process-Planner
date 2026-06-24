"""Session folder and artifact path policy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

SESSION_JSON_NAME = "session.json"
CAPTURE_CSV_NAME = "captures.csv"


@dataclass(frozen=True)
class SessionPaths:
    """Resolved filesystem locations for one session folder."""

    folder: Path

    @classmethod
    def for_folder(cls, folder: Path) -> SessionPaths:
        """Build session paths from a user-selected folder."""

        return cls(folder=Path(folder).expanduser().resolve())

    @property
    def session_json(self) -> Path:
        """Return the canonical session JSON path."""

        return self.folder / SESSION_JSON_NAME

    @property
    def capture_csv(self) -> Path:
        """Return the capture summary CSV path."""

        return self.folder / CAPTURE_CSV_NAME

    @property
    def images_dir(self) -> Path:
        """Return the managed image artifact directory."""

        return self.folder / "images"

    @property
    def drawings_dir(self) -> Path:
        """Return the managed editable drawing spec directory."""

        return self.folder / "drawings"

    @property
    def reports_dir(self) -> Path:
        """Return the managed report artifact directory."""

        return self.folder / "reports"

    @property
    def process_outputs_dir(self) -> Path:
        """Return the managed process-output artifact directory."""

        return self.folder / "process_outputs"

    def ensure_created(self) -> None:
        """Create the session folder and standard artifact directories."""

        self.folder.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.drawings_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.process_outputs_dir.mkdir(parents=True, exist_ok=True)


def normalize_artifact_path(path: str) -> str:
    """Return a portable session-relative artifact path."""

    text = path.strip().replace("\\", "/")
    if not text:
        raise ValueError("Artifact path must not be empty.")
    pure = PurePosixPath(text)
    first_part = pure.parts[0] if pure.parts else ""
    if pure.is_absolute() or ":" in first_part:
        raise ValueError(f"Artifact path must be relative to the session folder: {path}")
    if any(part == ".." for part in pure.parts):
        raise ValueError(f"Artifact path must not contain parent traversal: {path}")
    return pure.as_posix()


def artifact_path_to_disk(session_folder: Path, artifact_path: str) -> Path:
    """Resolve a session-relative artifact path safely onto disk."""

    normalized = normalize_artifact_path(artifact_path)
    root = Path(session_folder).resolve()
    destination = (root / normalized).resolve()
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Artifact path escapes the session folder: {artifact_path}") from exc
    return destination
