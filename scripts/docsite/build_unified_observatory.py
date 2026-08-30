#!/usr/bin/env python3
"""Build the root-only, default-off Unified Observatory Candidate."""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
for component in ("project-orrery-core", "project-orrery-observatory", "project-orrery-cli"):
    source = ROOT / "packages" / component / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

import build_personal_observatory  # noqa: E402
import build_workstream_relation_graph  # noqa: E402
from project_orrery_cli.authority_consumer import inspect_managed_consumer  # noqa: E402
from project_orrery_core import inspect_operating_rules  # noqa: E402
from project_orrery_observatory.display_vocabulary import NAVIGATION_LABELS  # noqa: E402
from project_orrery_observatory.fact_rules_projection import (  # noqa: E402
    build_fact_rules_projection,
    project_project_principles,
)
from project_orrery_observatory.team_observatory import inject_team_observatory  # noqa: E402
from project_orrery_observatory.unified_observatory import (  # noqa: E402
    ConsumerRegistration,
    inject_unified_shell,
    quarantine,
    validate_registrations,
)


def _registration(
    consumer_id: str,
    identity: str,
    label: str,
    order: int,
    route: str | None,
    capabilities: tuple[str, ...],
    privilege: str,
    source_id: str,
    source_version: str,
    *,
    network: str = "zero-network",
    required: bool = False,
    status: str = "available",
    reason: str | None = None,
) -> ConsumerRegistration:
    return ConsumerRegistration(
        consumer_id=consumer_id,
        consumer_version="root-candidate-v1",
        shell_api_versions=(1,),
        navigation_identity=identity,
        navigation_label=label,
        navigation_order=order,
        route_prefix=route,
        capabilities=capabilities,
        transport="local-loopback" if route else "static-or-loopback",
        network=network,
        privilege=privilege,
        authority="derived-control-view" if privilege != "read-only" else "derived-read-only",
        static_fallback="read-only" if privilege == "read-only" else "read-only-unavailable",
        failure_policy="fail-shell" if required else "quarantine-consumer",
        source_contract_id=source_id,
        source_contract_version=source_version,
        required=required,
        status=status,
        reason=reason,
    )


def default_registrations(
    *,
    mode: str,
    ai_available: bool | None = None,
) -> tuple[ConsumerRegistration, ...]:
    dynamic = mode == "dynamic"
    ai_ready = dynamic and ai_available is True
    registrations = (
        _registration(
            "shell-summary", "overview", NAVIGATION_LABELS["overview"], 10, None,
            ("read-status",), "read-only", "unified-observatory-shell", "v1", required=True,
        ),
        _registration(
            "canonical-docsite", "docs", NAVIGATION_LABELS["docs"], 20, "/api/v1/docs",
            ("read-docs", "search-docs"), "read-only", "build-docsite", "legacy-reader-v1", required=True,
        ),
        _registration(
            "ask-docs", "ask", NAVIGATION_LABELS["ask"], 30, "/api/v1/ai",
            ("read-derived-view", "configure-provider", "ask-provider", "refresh-derived-view"),
            "provider-opt-in", "broker-only-docsite", "v1", network="provider-opt-in",
            status="available" if ai_ready else "unavailable",
            reason=(
                None if ai_ready else
                "当前运行环境尚未安全启用模型服务。"
                if dynamic else
                "静态文件没有服务、凭据、cookie 或模型控制能力。"
            ),
        ),
        _registration(
            "authority-managed", "authority", NAVIGATION_LABELS["authority"], 40, "/api/v1/authority",
            ("read-status", "read-derived-view"), "read-only", "authority-managed-consumer", "v1",
        ),
        _registration(
            "personal-observatory", "personal", NAVIGATION_LABELS["personal"], 50, "/api/v1/personal",
            ("read-status",), "read-only", "personal-observatory-projection", "v1",
        ),
        _registration(
            "team-observatory", "team", NAVIGATION_LABELS["team"], 60, "/api/v1/team",
            ("read-status", "enable-team", "manage-local-transport", "send-request", "decide-request", "share-metadata"),
            "team-opt-in-request-only", "team-read-only-projection", "v1", network="team-opt-in",
            status="available" if dynamic else "unavailable",
            reason=None if dynamic else "静态文件不能启用团队模式或启动连接。",
        ),
        _registration(
            "workstream-graph", "workstreams", NAVIGATION_LABELS["workstreams"], 70, "/api/v1/workstreams",
            ("read-graph",), "read-only", "project-orrery-core.workstream-relations", "provider-schema-1",
        ),
        _registration(
            "workspace-maintenance", "maintenance", NAVIGATION_LABELS["maintenance"], 80, "/api/v1/maintenance",
            ("read-status", "background-refresh", "target-preflight", "local-remove-worktree"),
            "host-local-action-specific", "maintenance-provider", "maintenance-v2",
            status="available" if dynamic else "unavailable",
            reason=None if dynamic else "静态文件没有本机操作权限。",
        ),
    )
    return validate_registrations(registrations)


def _replace_registration(
    registrations: list[ConsumerRegistration],
    consumer_id: str,
    value: ConsumerRegistration,
) -> None:
    index = next(i for i, item in enumerate(registrations) if item.consumer_id == consumer_id)
    registrations[index] = value


def render_unified_site(
    project_root: Path,
    *,
    mode: str,
    title: str = "Orrery · Documentation",
    ai_available: bool | None = None,
) -> tuple[
    str,
    dict[str, Any],
    tuple[ConsumerRegistration, ...],
    dict[str, Any] | None,
    dict[str, Any] | None,
    dict[str, Any],
]:
    root = Path(project_root).resolve()
    if root != ROOT.resolve():
        raise ValueError("Unified Observatory Candidate is root-only")
    if mode not in {"static", "dynamic"}:
        raise ValueError("mode must be static or dynamic")
    registrations = list(default_registrations(mode=mode, ai_available=ai_available))
    dynamic = mode == "dynamic"

    previous_personal = os.environ.get("ORRERY_PERSONAL_OBSERVATORY_VIEW")
    os.environ["ORRERY_PERSONAL_OBSERVATORY_VIEW"] = "1"
    try:
        page, stats, _legacy_authority, personal = build_personal_observatory.render_personal_site(
            root / "docs", root / "AGENTS.md", root, title,
            maintenance_control_available=dynamic,
            maintenance_api_base="/api/v1/maintenance",
            maintenance_refresh_path="/refresh",
            maintenance_remove_path="/remove-worktree",
            maintenance_reload_after_action=False,
            include_local_worktrees=False,
        )
    finally:
        if previous_personal is None:
            os.environ.pop("ORRERY_PERSONAL_OBSERVATORY_VIEW", None)
        else:
            os.environ["ORRERY_PERSONAL_OBSERVATORY_VIEW"] = previous_personal
    if personal is None or personal.get("status") == "unavailable":
        item = next(value for value in registrations if value.consumer_id == "personal-observatory")
        _replace_registration(
            registrations, item.consumer_id,
            replace(item, status="unavailable", reason="个人工作台数据暂不可用。"),
        )

    team_item = next(value for value in registrations if value.consumer_id == "team-observatory")
    try:
        page = inject_team_observatory(
            page, api_base="/api/v1/team", dynamic_control=dynamic,
        )
    except Exception as error:
        _replace_registration(registrations, team_item.consumer_id, quarantine(team_item, error))

    graph_item = next(value for value in registrations if value.consumer_id == "workstream-graph")
    graph_provider_payload: dict[str, Any] | None = None
    previous_graph = os.environ.get("ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW")
    os.environ["ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW"] = "1"
    try:
        graph_provider_payload = build_workstream_relation_graph.core_relation_provider(root)
        page, graph = build_workstream_relation_graph.inject_enabled_relation_graph(
            page, root, provider=lambda: graph_provider_payload or {},
        )
        if graph is None or graph.get("status") == "unavailable":
            _replace_registration(
                registrations, graph_item.consumer_id,
                replace(graph_item, status="unavailable", reason="当前没有可显示的完整任务关系证据。"),
            )
    except Exception as error:
        _replace_registration(registrations, graph_item.consumer_id, quarantine(graph_item, error))
    finally:
        if previous_graph is None:
            os.environ.pop("ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW", None)
        else:
            os.environ["ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW"] = previous_graph

    authority_status: dict[str, Any] | None = None
    authority_reason: str | None = None
    fact_rules_projection = build_fact_rules_projection(
        project_principles=project_project_principles(root / "docs" / "core" / "principles.md"),
        operating_rules_capability=inspect_operating_rules(),
    )
    authority_item = next(value for value in registrations if value.consumer_id == "authority-managed")
    try:
        authority_status = inspect_managed_consumer(
            root,
            requested_selection="legacy",
            selection_authority="system-default",
            fact_scope="candidate",
            evidence_visibility=("revision-content", "human-or-agent-assertion"),
        )
    except Exception as error:
        quarantined = quarantine(authority_item, error)
        _replace_registration(registrations, authority_item.consumer_id, quarantined)
        authority_reason = quarantined.reason

    registrations = list(validate_registrations(registrations))
    page = inject_unified_shell(
        page, registrations, mode=mode,
        authority_status=authority_status, authority_reason=authority_reason,
        fact_rules_projection=fact_rules_projection,
    )
    return page, stats, tuple(registrations), authority_status, graph_provider_payload, fact_rules_projection


def main() -> None:
    parser = argparse.ArgumentParser(description="Build root-only Unified Observatory Candidate")
    parser.add_argument("--out", default=str(ROOT / "docs" / "_site" / "unified-observatory.html"))
    parser.add_argument("--title", default="Orrery · Documentation")
    parser.add_argument("--enable", action="store_true")
    arguments = parser.parse_args()
    if not arguments.enable:
        raise SystemExit("Unified Observatory is root-only/default-off; pass --enable explicitly")
    page, stats, registrations, _authority, _graph, _facts_rules = render_unified_site(
        ROOT, mode="static", title=arguments.title,
    )
    output = Path(arguments.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    print(f"Unified Observatory static Candidate: {output}")
    print(
        "  adrs: %(adrs)d | states: %(states)d | docs: %(documents)d | consumers: "
        % stats + str(len(registrations))
    )
    print("  static: read-only · no server · no cookie · no control")


if __name__ == "__main__":
    main()
