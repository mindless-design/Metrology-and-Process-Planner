"""Development bootstrap macro for KLayout.

Place or symlink this file into KLayout's Python macro folder, then update
REPO_ROOT if the file is copied outside the repository.
"""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PACKAGE_ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from metrology_process_planner.infrastructure.klayout.plugin import register_plugin

register_plugin()
