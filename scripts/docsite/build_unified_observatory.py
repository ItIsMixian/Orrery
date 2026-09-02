#!/usr/bin/env python3
"""Build the root-only, default-off Unified Observatory Candidate."""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
for component in ("project-orrery-core", "project-orrery-observatory", "project-orrery-cli"):
    source = ROOT / "packages" / component / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

import build_personal_observatory  # noqa: E402
from project_orrery_cli.authority_consumer import inspect_managed_consumer  # noqa: E402
from project_orrery_core import inspect_operating_rules  # noqa: E402
from project_orrery_observatory.display_vocabulary import NAVIGATION_LABELS  # noqa: E402
from project_orrery_observatory.fact_rules_projection import (  # noqa: E402
    build_fact_rules_projection,
    project_project_principles,
)
from project_orrery_observatory.relation_inbox import inject_relation_inbox  # noqa: E402
from project_orrery_observatory.personal_observatory import inject_personal_observatory  # noqa: E402
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
            (("read-status", "inspect-relations", "confirm-local-relation") if dynamic else ("read-status", "inspect-relations")),
            "host-local-action-specific" if dynamic else "read-only", "personal-observatory-projection", "v1",
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
            ("read-graph", "inspect-relations"), "read-only", "project-orrery-core.workstream-relations", "provider-schema-2",
        ),
        _registration(
            "workspace-maintenance", "maintenance", NAVIGATION_LABELS["maintenance"], 80, "/api/v1/maintenance",
            ("read-status", "background-refresh", "target-preflight", "local-remove-worktree"),
            "host-local-action-specific", "maintenance-provider", "maintenance-v2",
            status="available" if dynamic else "unavailable",
            reason=None if dynamic else "静态文件没有本机操作权限。",
        ),
        _registration(
            "routes-and-trends", "trends", NAVIGATION_LABELS["trends"], 90, None,
            ("read-derived-view",), "read-only", "build-docsite", "legacy-reader-v1",
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


def relation_capture_payload(root: Path) -> dict[str, Any]:
    from project_orrery_core.workstream_relation_capture import inspect_relation_capture

    capture = inspect_relation_capture(root)
    pending = []
    for item in capture.get("pending_proposals", []):
        projected = dict(item)
        if not isinstance(projected.get("local_confirmation"), Mapping):
            projected["local_confirmation"] = {
                "allowed": False,
                "reason_code": "local-human-authority-unavailable",
                "read_only": True,
                "writes_performed": False,
            }
        pending.append(projected)
    capture["pending_proposals"] = pending
    capture["local_actions_require_same_origin_cookie"] = True
    capture["central_request_only"] = True
    return capture


def _dynamic_shell_base(
    root: Path,
    *,
    title: str,
    base_site: tuple[str, dict[str, Any], dict[str, Any] | None] | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
    """Compose the document shell with bounded local placeholders for slower consumers."""
    if base_site is None:
        page, stats, authority = build_personal_observatory._base_site(
            root / "docs", root / "AGENTS.md", root, title,
        )
    else:
        page, stats, authority = base_site
    maintenance = {
        "status": "loading",
        "control_available": True,
        "api_base": "/api/v1/maintenance",
        "refresh_path": "/refresh",
        "remove_path": "/remove-worktree",
        "reload_after_action": False,
        "cache": {"entries": []},
        "queue": [],
        "authorizations": [],
        "receipts": [],
        "protected_reasons": {},
        "background_refresh": {"status": "pending"},
    }
    personal = {
        "schema_version": 1,
        "contract_type": "orrery-active-task-projection-v1",
        "status": "loading",
        "mode": "personal",
        "network_performed": False,
        "writes_performed": False,
        "captured_at": "pending",
        "revision": "pending",
        "counts": {"registry_worktrees": 0, "current": 0, "history": 0, "primary": 0, "refresh_needed": 0},
        "tasks": [],
        "maintenance": maintenance,
        "cache_summary_state": "unknown",
        "maintenance_error": None,
        "read_boundary": {
            "registry_calls": 0, "session_files_attempted": 0, "session_bytes_read": 0,
            "maintenance_cache_snapshots": 0, "worktree_source_files_read": 0,
            "scope_observations": 0, "diff_reads": 0, "startup_full_scan": False, "elapsed_ms": 0,
        },
        "dynamic": True,
    }
    page = inject_personal_observatory(page, personal)
    auto_refresh = (
        '<script>window.setTimeout(()=>{const button=document.querySelector("[data-active-task-refresh]");'
        'if(button&&!button.disabled)button.click()},0)</script>'
    )
    return page.replace("</body>", auto_refresh + "</body>", 1), stats, authority, personal


def graph_provider_payload(root: Path) -> dict[str, Any]:
    """Load the heavy Graph provider only inside explicit eager/background activation."""
    module = importlib.import_module("build_workstream_relation_graph")
    return module.core_relation_provider(root)


def _inject_dynamic_graph_slot(page: str) -> tuple[str, dict[str, Any]]:
    content_marker = '</main><aside class="toc" id="toc">'
    nav_candidates = (
        '<a class="nav-item" data-target="team-observatory"><span class="dot proposed"></span><span class="lbl">团队协作</span></a>',
        '<a class="nav-item" data-target="personal-observatory"><span class="dot state"></span><span class="lbl">个人工作台</span></a>',
    )
    marker = next((item for item in nav_candidates if item in page), None)
    if marker is None or content_marker not in page or "</style>" not in page:
        raise ValueError("dynamic Graph slot composition markers are missing")
    nav = '<a class="nav-item" data-target="workstream-relation-graph"><span class="dot proposed"></span><span class="lbl">任务关系</span></a>'
    css = (
        '.wg-activation-shell{margin:0 auto;max-width:1180px}.wg-activation-card{min-height:280px;display:grid;'
        'place-items:center;padding:32px;border:1px solid var(--line);border-radius:12px;background:var(--bg2);text-align:center}'
        '.wg-activation-card b{display:block;margin-bottom:8px;font-size:18px}.wg-activation-card span{color:var(--mut);font-size:11px}'
    )
    panel = (
        '<article class="page wide wg-activation-shell" id="workstream-relation-graph" '
        'data-kind="workstream-relation-graph" data-title="任务关系" data-authority="derived-read-only" '
        'data-read-only="true" data-wg-delivery-state="loading"><section class="wg-activation-card" role="status">'
        '<div><b>任务关系正在本机加载</b><span>Orrery 其他页面已经可用；关系投影完成后仅更新本区域。</span></div>'
        '</section></article>'
    )
    result = page.replace("</style>", css + "</style>", 1)
    result = result.replace(marker, marker + nav, 1)
    result = result.replace(content_marker, panel + content_marker, 1)
    projection = {
        "projection_schema_version": 2,
        "contract_type": "workstream-relation-graph-observatory",
        "status": "loading",
        "authority": "derived-read-only",
        "read_only": True,
        "writes_performed": False,
        "network_performed": False,
        "execution_capability": False,
        "available_actions": [],
    }
    return result, projection


def render_unified_site(
    project_root: Path,
    *,
    mode: str,
    title: str = "Orrery · Documentation",
    ai_available: bool | None = None,
    base_site: tuple[str, dict[str, Any], dict[str, Any] | None] | None = None,
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

    if dynamic:
        page, stats, _legacy_authority, personal = _dynamic_shell_base(
            root, title=title, base_site=base_site,
        )
    else:
        previous_personal = os.environ.get("ORRERY_PERSONAL_OBSERVATORY_VIEW")
        os.environ["ORRERY_PERSONAL_OBSERVATORY_VIEW"] = "1"
        try:
            page, stats, _legacy_authority, personal = build_personal_observatory.render_personal_site(
                root / "docs", root / "AGENTS.md", root, title,
                maintenance_control_available=False,
                maintenance_api_base="/api/v1/maintenance",
                maintenance_refresh_path="/refresh",
                maintenance_remove_path="/remove-worktree",
                maintenance_reload_after_action=False,
                lightweight_active_tasks=True,
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

    capture_payload: dict[str, Any] | None = None
    try:
        capture_payload = (
            {
                "schema_version": 2,
                "contract_type": "workstream-relation-capture-inspection",
                "status": "loading",
                "pending_proposals": [],
                "read_only": True,
                "writes_performed": False,
                "network_performed": False,
                "local_actions_require_same_origin_cookie": True,
                "central_request_only": True,
            }
            if dynamic else relation_capture_payload(root)
        )
        page = inject_relation_inbox(page, capture_payload, dynamic=dynamic)
    except Exception as error:
        personal_item = next(value for value in registrations if value.consumer_id == "personal-observatory")
        _replace_registration(registrations, personal_item.consumer_id, quarantine(personal_item, error))

    graph_item = next(value for value in registrations if value.consumer_id == "workstream-graph")
    graph_provider_payload: dict[str, Any] | None = (
        {"relation_capture": capture_payload} if dynamic and capture_payload is not None else None
    )
    previous_graph = os.environ.get("ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW")
    os.environ["ORRERY_WORKSTREAM_RELATION_GRAPH_VIEW"] = "1"
    try:
        if dynamic:
            page, graph = _inject_dynamic_graph_slot(page)
        else:
            graph_builder = importlib.import_module("build_workstream_relation_graph")
            graph_provider_payload = graph_builder.core_relation_provider(root)
            if capture_payload is not None:
                graph_provider_payload["relation_capture"] = capture_payload
            page, graph = graph_builder.inject_enabled_relation_graph(
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
    if dynamic:
        authority_reason = "管理状态将在首次打开时从本机权威输入加载。"
    else:
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
