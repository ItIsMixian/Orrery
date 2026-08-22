"""Unified source-checkout entry point for the Project Orrery CLI."""
from __future__ import annotations

import sys

from . import (
    authority_migrate,
    authority_restore,
    collaboration_contract,
    integration,
    review,
    scaffold,
    update,
    validate,
    worktree,
)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in {"-h", "--help"}:
        print(
            "usage: project-orrery "
            "{scaffold|validate|check-update|migrate-authority-model|"
            "restore-authority-model|collaboration-contract|worktree|integrate|review} [options]"
        )
        return 0
    command = arguments.pop(0)
    commands = {
        "scaffold": scaffold.main,
        "validate": validate.main,
        "check-update": update.main,
        "migrate-authority-model": authority_migrate.main,
        "restore-authority-model": authority_restore.main,
        "collaboration-contract": collaboration_contract.main,
        "worktree": worktree.main,
        "integrate": integration.main,
        "review": review.main,
    }
    selected = commands.get(command)
    if selected is None:
        print(f"ERROR: unknown command: {command}", file=sys.stderr)
        return 2
    return selected(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
