"""Cross-platform options for production child processes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _audit(options: dict[str, Any], *, enabled: bool) -> None:
    target = os.environ.get("ORRERY_CHILD_POLICY_AUDIT_PATH")
    if not target:
        return
    caller = sys._getframe(2)
    record = {
        "schema_version": 1,
        "contract_type": "orrery-child-process-policy-audit-v1",
        "pid": os.getpid(),
        "os_name": os.name,
        "enabled": enabled,
        "creationflags": int(options.get("creationflags", 0)),
        "caller_file": Path(caller.f_code.co_filename).name,
        "caller_function": caller.f_code.co_name,
        "recorded_at": time.time(),
    }
    try:
        with Path(target).open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    except OSError:
        pass


def no_window_options(*, enabled: bool = True) -> dict[str, Any]:
    """Hide console-subsystem children on Windows and leave other hosts unchanged."""
    options = (
        {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}
        if enabled and os.name == "nt" else {}
    )
    _audit(options, enabled=enabled)
    return options
