"""Build a clean KLayout package archive."""

from __future__ import annotations

import argparse
import shutil
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from tools.package_manifest import iter_release_files

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"


def build_package(destination: Optional[Path] = None) -> Path:
    """Build a zip archive containing only release package files."""

    archive_path = destination or _default_archive_path()
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        archive_path.unlink()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in iter_release_files(PROJECT_ROOT):
            archive.write(path, path.relative_to(PROJECT_ROOT).as_posix())
    return archive_path


def stage_package(destination: Path) -> Path:
    """Copy release package files into a clean directory tree."""

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for source in iter_release_files(PROJECT_ROOT):
        target = destination / source.relative_to(PROJECT_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return destination


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the package builder from the command line."""

    parser = argparse.ArgumentParser(description="Build the KLayout package archive.")
    parser.add_argument("--output", type=Path, help="Optional zip archive destination.")
    args = parser.parse_args(argv)
    archive = build_package(args.output)
    print(archive)
    return 0


def _default_archive_path() -> Path:
    return DIST_DIR / "metrology_process_planner.zip"


if __name__ == "__main__":
    raise SystemExit(main())

