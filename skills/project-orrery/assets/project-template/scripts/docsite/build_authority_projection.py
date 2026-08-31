#!/usr/bin/env python3
"""Build the root-only M2.2 Authority Candidate Observatory projection.

This managed integration entry is intentionally separate from
``build_docsite.py``.  The normal builder remains the byte-identical released
tool, while this source-checkout-only entry may import both the CLI collector
and Observatory projection without creating a package dependency cycle.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from pathlib import Path

import build_docsite


def authority_projection_enabled() -> bool:
    return os.environ.get("ORRERY_AUTHORITY_PROJECTION_VIEW", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _enable_candidate_package_sources(root: Path) -> None:
    """Expose checkout packages only after explicit Candidate opt-in."""

    for component in (
        "project-orrery-core",
        "project-orrery-observatory",
        "project-orrery-cli",
    ):
        source = str(root / "packages" / component / "src")
        if source not in sys.path:
            sys.path.insert(0, source)


def _authority_evidence_visibility(default_visibility):
    raw = os.environ.get("ORRERY_AUTHORITY_EVIDENCE_VISIBILITY", "").strip()
    if not raw:
        return tuple(default_visibility)
    values = tuple(value.strip() for value in raw.split(",") if value.strip())
    if not values or len(values) != len(set(values)):
        raise ValueError("Authority evidence visibility must be a unique CSV list")
    return values


def _claim_json(value) -> str:
    return html.escape(
        json.dumps(value, ensure_ascii=False, sort_keys=True), quote=True
    )


def build_authority_candidate_projection_panel(projection: dict) -> str:
    """Render only a validated projection model; never parse document prose."""

    if projection.get("status") != "ready":
        raise ValueError("Authority Candidate projection is not ready")
    conformance = projection["conformance_input"]
    graph = projection["decision_graph"]
    effective = graph.get("effective_decisions")
    if effective is None:
        effective_html = '<span class="chip">Unknown</span>'
    else:
        effective_html = " ".join(
            '<a class="chip" href="#adr-%s">%s</a>'
            % (
                html.escape(item.removeprefix("ADR-").lower(), quote=True),
                html.escape(item, quote=True),
            )
            for item in effective
        )

    role_labels = {
        "seed": "Seed",
        "adr": "ADR",
        "design": "Design",
        "plan": "Plan",
        "state": "State",
        "validation": "Validation",
        "snapshot": "Snapshot",
    }
    role_sections = []
    for role, label in role_labels.items():
        documents = projection["roles"].get(role, [])
        cards = []
        for document in documents:
            evidence = document.get("evidence_provenance", [])
            visible = [
                item.get("category", "Unknown")
                for item in evidence
                if item.get("visible") is True
            ]
            cards.append(
                '<details style="margin:8px 0;padding:8px 10px;border:1px solid var(--line);'
                'border-radius:9px"><summary><b>%s</b> <span class="chip">%s</span></summary>'
                '<div style="margin-top:8px;font-size:12px;line-height:1.65">'
                'source: <a href="%s">%s</a><br>sha256: <code>%s</code><br>'
                "claims: <code>%s</code><br>relations: <code>%s</code><br>"
                "evidence visible: <code>%s</code><br>must not infer: <code>%s</code>"
                "</div></details>"
                % (
                    html.escape(document["subject"], quote=True),
                    html.escape(label, quote=True),
                    html.escape(document["source_href"], quote=True),
                    html.escape(document["source"], quote=True),
                    html.escape(document["source_sha256"], quote=True),
                    _claim_json(document["claims"]),
                    _claim_json(document["relations"]),
                    _claim_json(visible or ["Unknown"]),
                    _claim_json(document["must_not_infer"]),
                )
            )
        role_sections.append(
            '<details style="margin:10px 0"><summary><b>%s</b> · %d</summary>%s</details>'
            % (html.escape(label, quote=True), len(documents), "".join(cards))
        )

    return (
        '<section id="authority-candidate-projection" '
        'data-view-type="authority-candidate-projection" '
        'data-authoritative-source="core-owned-semantics" '
        'data-creates-project-facts="false" data-production-switched="false" '
        'style="margin:0 0 16px;padding:16px;border:1px solid #5795d6;'
        'border-radius:12px;background:rgba(87,149,214,.08)">'
        '<h2 style="margin:0 0 8px">🪐 Authority Candidate Projection</h2>'
        '<p style="margin:0 0 10px">显式启用的 M2.2 只读候选投影；默认 Observatory '
        "未切换，本视图不创建项目事实。关闭 <code>ORRERY_AUTHORITY_PROJECTION_VIEW</code> 即回滚。</p>"
        '<div style="display:flex;gap:8px;flex-wrap:wrap">'
        '<span class="chip">model: %s</span><span class="chip">scope: %s</span>'
        '<span class="chip">visibility: %s</span><span class="chip">reconciliation: %s</span>'
        '</div><p style="font-size:12px;overflow-wrap:anywhere">snapshot: <code>%s</code><br>'
        "bundle: <code>%s</code></p><h3>Effective decisions</h3><p>%s</p>"
        "<h3>Role claims 与来源</h3>%s"
        '<p style="font-size:12px;opacity:.8">Unknown 保持 Unknown；legacy prose、AI 与 insights '
        "均不是本页 claims 来源。</p></section>"
        % (
            html.escape(conformance["authority_model_version"], quote=True),
            html.escape(conformance["fact_scope"], quote=True),
            html.escape(", ".join(conformance["evidence_visibility"]), quote=True),
            html.escape(projection["reconciliation"]["status"], quote=True),
            html.escape(conformance["repository_snapshot"], quote=True),
            html.escape(projection["reconciliation"]["bundle_sha256"], quote=True),
            effective_html,
            "".join(role_sections),
        )
    )


def inject_authority_candidate_projection(page: str, projection: dict) -> str:
    marker = (
        '<article class="page wide on" id="dashboard" '
        'data-kind="dashboard" data-title="总览">'
    )
    if marker not in page:
        raise ValueError("dashboard projection marker not found")
    panel = build_authority_candidate_projection_panel(projection)
    return page.replace(marker, marker + panel, 1)


def render_candidate_site(
    docs_dir: Path,
    agents_file: Path,
    root: Path,
    title: str,
):
    """Render an opt-in projection or fail closed to the legacy page."""

    legacy_page, legacy_stats = build_docsite.render_site(
        docs_dir, agents_file, root, title
    )
    if not authority_projection_enabled():
        return legacy_page, legacy_stats, None

    fact_scope = (
        os.environ.get("ORRERY_AUTHORITY_FACT_SCOPE", "unknown").strip() or "unknown"
    )
    fixture_version = "unavailable"
    try:
        _enable_candidate_package_sources(root)
        from project_orrery_cli.authority_observations import (
            DEFAULT_EVIDENCE_VISIBILITY,
            authority_observation_snapshot,
            build_cli_authority_contract,
        )
        from project_orrery_core.authority import evaluate_authority
        from project_orrery_core.authority_compatibility import (
            AUTHORITY_MODEL_FIXTURE_IDS,
            judge_project_authority_model,
        )
        from project_orrery_observatory.authority_projection import (
            build_authority_projection,
        )

        manifest = json.loads(
            (root / ".project-orrery.json").read_text(encoding="utf-8")
        )
        capability = judge_project_authority_model(manifest)
        selected_version = capability.get("selected_version")
        fixture_version = AUTHORITY_MODEL_FIXTURE_IDS.get(
            selected_version, "unavailable"
        )
        if (
            capability.get("status") != "supported"
            or capability.get("authority_evaluation_capability") != "available"
            or fixture_version == "unavailable"
        ):
            raise ValueError("Authority Model is not available for projection")
        evidence_visibility = _authority_evidence_visibility(
            DEFAULT_EVIDENCE_VISIBILITY
        )
        expected_snapshot = authority_observation_snapshot(root)
        bundle = build_cli_authority_contract(
            root,
            evaluator=evaluate_authority,
            authority_model_version=fixture_version,
            fact_scope=fact_scope,
            evidence_visibility=evidence_visibility,
        )
        projection = build_authority_projection(
            bundle,
            authority_model_version=fixture_version,
            repository_snapshot=expected_snapshot,
            fact_scope=fact_scope,
            evidence_visibility=evidence_visibility,
        )
        page = inject_authority_candidate_projection(legacy_page, projection)
    except Exception as error:
        try:
            from project_orrery_observatory.authority_projection import (
                unavailable_projection,
            )

            projection = unavailable_projection(
                authority_model_version=fixture_version,
                fact_scope=fact_scope,
                error=error,
            )
        except Exception:
            projection = {
                "projection_schema": "observatory-authority-projection-v1",
                "status": "unavailable",
                "mode": "candidate-opt-in",
                "creates_project_facts": False,
                "production_behavior_switched": False,
                "fact_scope": fact_scope,
                "error": {"type": type(error).__name__, "message": str(error)},
            }
        return legacy_page, legacy_stats, {"authority_projection": projection}
    return page, legacy_stats, {"authority_projection": projection}


def main() -> None:
    here = Path(__file__).resolve()
    root = here.parents[2]
    parser = argparse.ArgumentParser(
        description="Build the root-only Authority Candidate Observatory projection."
    )
    parser.add_argument("--docs", default=str(root / "docs"))
    parser.add_argument("--agents", default=str(root / "AGENTS.md"))
    parser.add_argument("--out", default=str(root / "docs" / "_site" / "index.html"))
    parser.add_argument("--title", default="Orrery · Documentation")
    args = parser.parse_args()

    page, stats, projection = render_candidate_site(
        Path(args.docs), Path(args.agents), root, args.title
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print("doc viewer built:")
    print("  output : %s  (%.0f KB)" % (out, out.stat().st_size / 1024))
    print(
        "  adrs : %(adrs)d | states : %(states)d | subsys : %(subs)d | snaps : %(snaps)d | docs : %(documents)d | plans : %(plans)d | library : %(library)d"
        % stats
    )
    if projection is not None:
        print(
            "  authority projection : %s"
            % projection["authority_projection"].get("status", "unavailable")
        )


if __name__ == "__main__":
    main()
