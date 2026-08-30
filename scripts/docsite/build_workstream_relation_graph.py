#!/usr/bin/env python3
"""Build the root-only, default-off W7C-B Workstream relation graph page."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Mapping


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
for component in ("project-orrery-core", "project-orrery-observatory", "project-orrery-cli"):
    source = ROOT / "packages" / component / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

import build_personal_observatory
from project_orrery_observatory.workstream_relation_graph import (
    inject_workstream_relation_graph,
    project_core_relation_graph,
    write_projection_json,
)


SYNTHETIC_BROWSER_FIXTURE = (
    ROOT / "tests" / "fixtures" / "workstream-relations" / "v1" / "succession-chain.json"
)


def relation_graph_enabled() -> bool:
    return os.environ.get("ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW", "").strip().lower() in {
        "1", "true", "yes", "on"
    }


def core_relation_provider(project_root: Path) -> dict[str, Any]:
    """Return only the W7A Core graph and plan, without creating the relation root."""
    from project_orrery_core.workstream_relations import (
        build_succession_plan,
        load_relation_graph,
        relation_storage_root,
    )
    from project_orrery_core.workstream_relation_capture import (
        capture_storage_root,
        inspect_relation_capture,
        inspect_task_series,
    )

    root = Path(project_root).resolve()
    relation_root_present = relation_storage_root(root).is_dir()
    graph = load_relation_graph(root, include_legacy=True)
    plan = build_succession_plan(graph)
    payload = {
        "provider_schema_version": 1,
        "provider_id": "project-orrery-core.workstream-relations",
        "relation_root_present": relation_root_present,
        "authority": "derived-read-only",
        "graph": graph,
        "succession_plan": plan,
        "task_series": inspect_task_series(root),
    }
    if capture_storage_root(root).is_dir():
        payload["relation_capture"] = inspect_relation_capture(root)
    return payload


def synthetic_browser_provider() -> dict[str, Any]:
    """Map a fixed non-authoritative browser fixture through the real W7A Core builders."""
    from project_orrery_core.workstream_relations import (
        build_relation_graph,
        build_relation_record,
        build_succession_plan,
        default_relation_evidence,
    )

    fixture = json.loads(SYNTHETIC_BROWSER_FIXTURE.read_text(encoding="utf-8"))
    if fixture.get("schema_version") != 1 or not str(fixture.get("fixture_id", "")).startswith("workstream-relations-v1-sanitized"):
        raise ValueError("W7A synthetic browser fixture boundary is invalid")
    extra_nodes = [
        {
            "workstream_id": "waiting-task", "status": "inactive", "session_state": "current",
            "lifecycle_phase": "implementing", "runtime_condition": "waiting-for-user",
            "evidence_freshness": "current", "head_oid": "1" * 40, "scope_status": "current",
            "closure_reason": None, "primary_subsystem_id": "documentation-system",
            "affected_subsystem_ids": [], "visibility": "worktree-local", "observability": "local",
            "source_links": [{"kind": "workstream-session", "ref": "fixture:waiting-task"}], "origin": "native",
        },
        {
            "workstream_id": "blocked-task", "status": "blocked", "session_state": "current",
            "lifecycle_phase": "validating", "runtime_condition": "blocked-by-conflict",
            "evidence_freshness": "current", "head_oid": "2" * 40, "scope_status": "current",
            "closure_reason": None, "primary_subsystem_id": "release-and-toolchain",
            "affected_subsystem_ids": ["test-coverage"], "visibility": "worktree-local", "observability": "local",
            "source_links": [{"kind": "validation", "ref": "docs/validation/2026-08-28-dynamic-workstream-succession-contract.md"}], "origin": "native",
        },
        {
            "workstream_id": "failed-task", "status": "failed", "session_state": "current",
            "lifecycle_phase": "validating", "runtime_condition": "failed",
            "evidence_freshness": "current", "head_oid": "3" * 40, "scope_status": "current",
            "closure_reason": None, "primary_subsystem_id": "test-coverage",
            "affected_subsystem_ids": [], "visibility": "team-metadata", "observability": "local",
            "source_links": [{"kind": "workstream-session", "ref": "fixture:failed-task"}], "origin": "native",
        },
        {
            "workstream_id": "offline-unknown", "status": "unknown", "session_state": "current",
            "lifecycle_phase": "implementing", "runtime_condition": "offline",
            "evidence_freshness": "unknown", "head_oid": "4" * 40, "scope_status": "unknown",
            "closure_reason": None, "primary_subsystem_id": "multi-worktree-collaboration",
            "affected_subsystem_ids": [], "visibility": "team-metadata", "observability": "unavailable",
            "source_links": [{"kind": "workstream-session", "ref": "fixture:offline-unknown"}], "origin": "discovery",
        },
    ]
    extra_records = [
        build_relation_record(
            relation_id="rel-w5e-ci1-dependency", event_id="event-w5e-ci1-dependency", revision=1,
            relation_type="depends_on", source_workstream_id="W5E", target_workstream_id="CI1",
            lifecycle="active", recorded_at="2026-08-28T01:00:00Z", actor_kind="tool",
            actor_id="synthetic-browser-fixture", origin="discovery", reason="synthetic second dependency predecessor",
            evidence=default_relation_evidence(
                status="confirmed", source_head_oid="e" * 40, target_head_oid="d" * 40,
                source_head_status="current", target_head_status="current", scope_status="current",
                ancestry_status="not-applicable", dependency_status="confirmed",
            ),
            source_links=[{"kind": "validation", "ref": "docs/validation/2026-08-28-dynamic-workstream-succession-contract.md"}],
        ),
        build_relation_record(
            relation_id="rel-waiting-w5e", event_id="event-waiting-w5e", revision=1,
            relation_type="depends_on", source_workstream_id="waiting-task", target_workstream_id="W5E",
            lifecycle="proposed", recorded_at="2026-08-28T01:01:00Z", actor_kind="tool",
            actor_id="synthetic-browser-fixture", origin="discovery", reason="synthetic proposed dependency",
            evidence=default_relation_evidence(
                source_head_oid="1" * 40, target_head_oid="e" * 40,
                source_head_status="current", target_head_status="current", scope_status="current",
                ancestry_status="not-applicable", dependency_status="unknown",
            ), source_links=[{"kind": "relation", "ref": "fixture:waiting-w5e"}],
        ),
        build_relation_record(
            relation_id="rel-offline-w5e", event_id="event-offline-w5e", revision=1,
            relation_type="depends_on", source_workstream_id="offline-unknown", target_workstream_id="W5E",
            lifecycle="stale", recorded_at="2026-08-28T01:02:00Z", actor_kind="tool",
            actor_id="synthetic-browser-fixture", origin="discovery", reason="synthetic stale Unknown dependency",
            evidence=default_relation_evidence(
                status="stale", source_head_oid="4" * 40, target_head_oid="e" * 40,
                source_head_status="unknown", target_head_status="current", scope_status="unknown",
                ancestry_status="not-applicable", dependency_status="stale",
            ), source_links=[{"kind": "relation", "ref": "fixture:offline-w5e"}],
        ),
    ]
    graph = build_relation_graph(
        [*fixture["records"], *extra_records],
        nodes=[*fixture["nodes"], *extra_nodes],
        pair_constraints=[
            {"left_workstream_id": "CI2-late", "right_workstream_id": "W5E", "reasons": ["direct-path-overlap", "l3-exclusive-resource"]},
            {"left_workstream_id": "failed-task", "right_workstream_id": "W5E", "reasons": ["semantic-overlap-proposed"]},
            {"left_workstream_id": "blocked-task", "right_workstream_id": "W5E", "reasons": ["direct-validation-surface", "l3"]},
        ],
    )
    plan = build_succession_plan(graph)
    return {
        "provider_schema_version": 1,
        "provider_id": "project-orrery-core.workstream-relations",
        "relation_root_present": True,
        "authority": "synthetic-non-authoritative",
        "graph": graph,
        "succession_plan": plan,
        "task_series": {
            "schema_version": 2,
            "contract_type": "workstream-task-series-inspection",
            "items": [
                {"workstream_id": "CI1", "series_id": "CI", "task_code": "CI1", "series_order": 1},
                {"workstream_id": "CI2-late", "series_id": "CI", "task_code": "CI2", "series_order": 2},
            ],
            "read_only": True,
            "writes_performed": False,
            "name_inference_performed": False,
        },
    }


def inject_enabled_relation_graph(
    page: str,
    project_root: Path,
    *,
    provider: Callable[[], Mapping[str, Any]] | None = None,
) -> tuple[str, Mapping[str, Any] | None]:
    root = Path(project_root).resolve()
    if root != ROOT.resolve():
        raise ValueError("Workstream relation graph entry is root-only")
    if not relation_graph_enabled():
        return page, None
    selected = provider or (lambda: core_relation_provider(root))
    projection = project_core_relation_graph(selected)
    return inject_workstream_relation_graph(page, projection), projection


def render_workstream_relation_graph_site(
    docs_dir: Path,
    agents_file: Path,
    project_root: Path,
    title: str,
    *,
    provider: Callable[[], Mapping[str, Any]] | None = None,
):
    root = Path(project_root).resolve()
    if root != ROOT.resolve():
        raise ValueError("Workstream relation graph entry is root-only")
    page, stats, authority, personal = build_personal_observatory.render_personal_site(
        Path(docs_dir), Path(agents_file), root, title
    )
    page, projection = inject_enabled_relation_graph(page, root, provider=provider)
    return page, stats, authority, personal, projection


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the root-only W7C-B Workstream relation graph Observatory page."
    )
    parser.add_argument("--docs", default=str(ROOT / "docs"))
    parser.add_argument("--agents", default=str(ROOT / "AGENTS.md"))
    parser.add_argument("--out", default=str(ROOT / "docs" / "_site" / "workstream-relations.html"))
    parser.add_argument("--title", default="Orrery · Documentation")
    parser.add_argument("--enable", action="store_true")
    parser.add_argument(
        "--synthetic-browser-fixture",
        action="store_true",
        help="Use the fixed synthetic-non-authoritative W7A Core fixture for browser acceptance.",
    )
    parser.add_argument("--snapshot-out", type=Path)
    arguments = parser.parse_args()
    if arguments.enable:
        os.environ["ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW"] = "1"
    provider = synthetic_browser_provider if arguments.synthetic_browser_fixture else None
    page, stats, authority, personal, projection = render_workstream_relation_graph_site(
        Path(arguments.docs), Path(arguments.agents), ROOT, arguments.title, provider=provider
    )
    out = Path(arguments.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    if arguments.snapshot_out and projection is not None:
        write_projection_json(arguments.snapshot_out, projection)
    print("workstream relation graph built:")
    print("  output : %s  (%.0f KB)" % (out, out.stat().st_size / 1024))
    print(
        "  adrs : %(adrs)d | states : %(states)d | subsys : %(subs)d | docs : %(documents)d"
        % stats
    )
    print("  personal projection : %s" % ("disabled" if personal is None else personal.get("status")))
    print("  relation graph : %s" % ("disabled" if projection is None else projection.get("status")))
    if authority is not None:
        print("  authority projection : composed")


if __name__ == "__main__":
    main()
