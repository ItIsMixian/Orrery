#!/usr/bin/env python3
"""Validate a sealed W5D acceptance run without modifying it."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from run_lan_collaboration_acceptance import validate_acceptance_run


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print("usage: validate_lan_collaboration_acceptance.py <run-root>", file=sys.stderr)
        return 2
    try:
        result = validate_acceptance_run(Path(arguments[0]))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"verdict": "failed", "error_type": type(exc).__name__}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
