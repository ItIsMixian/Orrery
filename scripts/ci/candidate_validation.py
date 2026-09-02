"""Record an existing validation result against one immutable frozen Candidate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE_SOURCE = ROOT / "packages" / "project-orrery-core" / "src"
sys.path.insert(0, str(CORE_SOURCE))

from project_orrery_core.candidate_freeze import (  # noqa: E402
    record_candidate_validation,
    request_candidate_validation,
)


def _load(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read validation result receipt: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("validation result receipt must contain a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append an exact-SHA Candidate validation receipt without running validation"
    )
    actions = parser.add_subparsers(dest="action", required=True)
    request = actions.add_parser("request", help="write an exact-SHA handoff to the existing CI7 router")
    request.add_argument("--target", type=Path, default=Path("."))
    request.add_argument("--freeze-receipt-id", required=True)
    record = actions.add_parser("record", help="consume an existing runner result receipt")
    record.add_argument("--target", type=Path, default=Path("."))
    record.add_argument("--freeze-receipt-id", required=True)
    record.add_argument("--result-receipt", required=True, type=Path)
    record.add_argument(
        "--stage", required=True,
        choices=("focused", "fast", "checkpoint", "candidate", "promotion"),
    )
    arguments = parser.parse_args(argv)
    try:
        if arguments.action == "request":
            receipt = request_candidate_validation(
                arguments.target, freeze_receipt_id=arguments.freeze_receipt_id
            )
        else:
            receipt = record_candidate_validation(
                arguments.target,
                freeze_receipt_id=arguments.freeze_receipt_id,
                result_receipt=_load(arguments.result_receipt),
                validation_stage=arguments.stage,
            )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    if arguments.action == "request":
        return 0
    return 0 if receipt["validation_status"] == "validated" else 4


if __name__ == "__main__":
    raise SystemExit(main())
