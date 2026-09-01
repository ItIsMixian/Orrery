"""Cross-platform options for production child processes."""
from __future__ import annotations

import os
import subprocess
from typing import Any


def no_window_options(*, enabled: bool = True) -> dict[str, Any]:
    """Hide console-subsystem children on Windows and leave other hosts unchanged."""
    if enabled and os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}
    return {}
