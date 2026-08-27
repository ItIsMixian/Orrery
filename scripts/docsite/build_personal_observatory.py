#!/usr/bin/env python3
"""Build the root-only, opt-in W4 Personal Observatory projection."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import build_authority_projection
import build_docsite


def personal_observatory_enabled() -> bool:
    return os.environ.get("ORRERY_PERSONAL_OBSERVATORY_VIEW", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _enable_candidate_package_sources(root: Path) -> None:
    for component in (
        "project-orrery-core",
        "project-orrery-observatory",
        "project-orrery-cli",
    ):
        source = str(root / "packages" / component / "src")
        if source not in sys.path:
            sys.path.insert(0, source)


def _base_site(docs_dir: Path, agents_file: Path, root: Path, title: str):
    if build_authority_projection.authority_projection_enabled():
        page, stats, authority = build_authority_projection.render_candidate_site(
            docs_dir, agents_file, root, title
        )
        return page, stats, authority
    return build_docsite._render_site_for_runtime(docs_dir, agents_file, root, title)


def render_personal_site(
    docs_dir: Path,
    agents_file: Path,
    root: Path,
    title: str,
    *,
    excluded_branches: tuple[str, ...] = (),
    maintenance_control_available: bool = False,
):
    """Return the base Observatory unchanged unless explicit W4 opt-in is enabled."""

    page, stats, authority = _base_site(docs_dir, agents_file, root, title)
    if not personal_observatory_enabled():
        return page, stats, authority, None
    _enable_candidate_package_sources(root)
    from project_orrery_observatory.personal_observatory import (
        build_personal_observatory_projection,
        inject_personal_observatory,
        unavailable_personal_observatory_projection,
    )

    try:
        from project_orrery_core.maintenance import (
            catch_up_maintenance_scan,
            maintenance_status,
        )

        catch_up_maintenance_scan(root)
        maintenance = maintenance_status(root)
        maintenance["control_available"] = maintenance_control_available
    except Exception as error:
        maintenance = {
            "status": "unavailable",
            "error": {"type": type(error).__name__, "message": str(error)},
            "control_available": maintenance_control_available,
            "queue": [],
            "authorizations": [],
            "receipts": [],
            "protected_reasons": {},
        }

    try:
        projection = build_personal_observatory_projection(
            root,
            include_local_worktrees=True,
            excluded_branches=excluded_branches,
            maintenance_projection=maintenance,
        )
        page = inject_personal_observatory(page, projection)
    except Exception as error:
        projection = unavailable_personal_observatory_projection(error)
        page = inject_personal_observatory(page, projection)
    return page, stats, authority, projection


def main() -> None:
    here = Path(__file__).resolve()
    root = here.parents[2]
    parser = argparse.ArgumentParser(
        description="Build the root-only W4 Personal Observatory projection."
    )
    parser.add_argument("--docs", default=str(root / "docs"))
    parser.add_argument("--agents", default=str(root / "AGENTS.md"))
    parser.add_argument("--out", default=str(root / "docs" / "_site" / "index.html"))
    parser.add_argument("--title", default="Project Orrery · Documentation")
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--exclude-branch", action="append", default=[])
    parser.add_argument("--snapshot-out", type=Path)
    args = parser.parse_args()
    if args.enable:
        os.environ["ORRERY_PERSONAL_OBSERVATORY_VIEW"] = "1"

    page, stats, authority, projection = render_personal_site(
        Path(args.docs),
        Path(args.agents),
        root,
        args.title,
        excluded_branches=tuple(args.exclude_branch),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    if args.snapshot_out and projection is not None:
        from project_orrery_observatory.personal_observatory import write_projection_json

        write_projection_json(args.snapshot_out, projection)
    print("personal observatory built:")
    print("  output : %s  (%.0f KB)" % (out, out.stat().st_size / 1024))
    print(
        "  adrs : %(adrs)d | states : %(states)d | subsys : %(subs)d | docs : %(documents)d"
        % stats
    )
    print("  personal projection : %s" % (
        "disabled" if projection is None else projection.get("status", "unavailable")
    ))
    if authority is not None:
        print("  authority projection : composed")


if __name__ == "__main__":
    main()
