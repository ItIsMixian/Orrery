"""Read-only portable operating-rules and Authority Route Preflight CLI."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from project_orrery_core.authority_route import (
    AuthorityRouteError,
    evaluate_authority_route,
    unavailable_route_receipt,
)
from project_orrery_core.operating_rules import inspect_operating_rules, load_operating_rules

from .protocol import JsonExitCode, emit, issue, response


_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_BACKTICK_PATH = re.compile(r"`([^`]+)`")
_SECTION = re.compile(r"(?ms)^##\s+([^\n]+)\n(.*?)(?=^##\s+|\Z)")
_ID = re.compile(r"\*\*ID\*\*:\s*`([^`]+)`")
_WHAT = re.compile(r"\*\*What\*\*:\s*([^\n]+)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the existing Authority Meta Model operating rules")
    actions = parser.add_subparsers(dest="action", required=True)
    inspect = actions.add_parser("inspect", help="inspect inventory capability without writing")
    inspect.add_argument("--inventory-version", type=int, default=1)
    inspect.add_argument("--inventory-file", type=Path)
    inspect.add_argument("--json", action="store_true", dest="json_output")
    route = actions.add_parser("route", help="run provider-neutral Authority Route Preflight")
    route.add_argument("--target", type=Path, default=Path("."))
    route.add_argument("--query", required=True)
    route.add_argument("--query-class")
    route.add_argument(
        "--fact-scope",
        choices=("canonical", "candidate", "worktree", "local-only", "historical", "unknown"),
        default="unknown",
    )
    route.add_argument("--json", action="store_true", dest="json_output")
    return parser


def _role(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized == "AGENTS.md":
        return "index"
    if normalized.startswith("docs/state/"):
        return "state"
    if normalized.startswith("docs/decisions/"):
        return "adr"
    if normalized.startswith("docs/design/"):
        return "design"
    if normalized.startswith("docs/validation/"):
        return "validation"
    if normalized.startswith("skills/") or normalized.startswith("adapters/"):
        return "distribution"
    if normalized.endswith("release-manifest.json") or "phase0_baseline" in normalized:
        return "release"
    if "templates/" in normalized or "project-template/" in normalized:
        return "template"
    return "implementation"


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9_.:-]+", "-", value.lower()).strip("-")
    return result or "source"


def _source(
    concept_id: str,
    path: str,
    role: str,
    rank: int,
    *,
    suffix: str | None = None,
    lower_authority: bool = False,
    required_for_axes: tuple[str, ...] = (),
) -> dict[str, Any]:
    identity = suffix or Path(path).stem
    return {
        "source_id": f"{concept_id}:{role}:{_slug(identity)}",
        "path": path.replace("\\", "/"),
        "role": role,
        "authority_rank": rank,
        "lower_authority": lower_authority,
        "required_for_axes": list(required_for_axes),
    }


def _deduplicate_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_ids: set[str] = set()
    seen_paths: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for source in sources:
        key = (source["path"], source["role"])
        if key in seen_paths:
            continue
        candidate = source["source_id"]
        serial = 2
        while candidate in seen_ids:
            candidate = f"{source['source_id']}:{serial}"
            serial += 1
        value = dict(source)
        value["source_id"] = candidate
        result.append(value)
        seen_ids.add(candidate)
        seen_paths.add(key)
    return result


def _portable_concepts(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    concepts: list[dict[str, Any]] = []
    for value in inventory["routing"]["portable_concepts"]:
        concept_id = value["concept_id"]
        sources: list[dict[str, Any]] = []
        for index, path in enumerate(value["minimum_governing_sources"]):
            sources.append(_source(
                concept_id, path, _role(path), 10 + index * 10,
                required_for_axes=("semantic_decision",),
            ))
        for index, path in enumerate(value.get("conditional_governing_sources", [])):
            sources.append(_source(concept_id, path, _role(path), 31 + index))
        if concept_id == "authority-meta-model":
            sources.extend(
                (
                    _source(concept_id, "docs/design/authority-meta-model.md", "design", 40),
                    _source(concept_id, "packages/project-orrery-core/src/project_orrery_core/authority.py", "implementation", 50, suffix="authority-evaluator", required_for_axes=("implementation",)),
                    _source(concept_id, "packages/project-orrery-core/src/project_orrery_core/operating_rules.py", "implementation", 51, suffix="operating-rules"),
                    _source(concept_id, "packages/project-orrery-core/src/project_orrery_core/authority_route.py", "implementation", 52, suffix="authority-route"),
                    _source(concept_id, "docs/validation/2026-08-30-a4-portable-operating-rules-and-authority-route-preflight.md", "validation", 60, suffix="a4-validation"),
                    _source(concept_id, "skills/project-orrery/references/orrery-operating-rules-v1.json", "distribution", 70, suffix="skill-operating-rules", required_for_axes=("distribution_consumer",)),
                    _source(concept_id, "skills/project-orrery/SKILL.md", "distribution", 71, suffix="skill-bootstrap", required_for_axes=("distribution_consumer",)),
                    _source(concept_id, "tests/fixtures/platform_neutral_phase0_baseline.json", "release", 80, suffix="public-v0.2.0", required_for_axes=("public_default_release",)),
                    _source(concept_id, "skills/project-orrery/assets/project-template/docs/core/principles.md", "template", 200, suffix="seed-template", lower_authority=True),
                )
            )
        concepts.append({
            "concept_id": concept_id,
            "subsystem_id": value["subsystem_id"],
            "aliases": list(value["aliases"]),
            "sources": _deduplicate_sources(sources),
        })
    return concepts


def _extract_state_implementation_paths(root: Path, relative: str) -> list[str]:
    path = root / relative
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    match = re.search(r"(?ms)^##\s+实现证据\s*$\n(.*?)(?=^##\s+|\Z)", text)
    if not match:
        return []
    candidates = []
    for value in _BACKTICK_PATH.findall(match.group(1)):
        normalized = value.replace("\\", "/").strip()
        if normalized and not normalized.startswith(("http://", "https://")) and "*" not in normalized:
            candidates.append(normalized.rstrip("/"))
    for value in _LINK.findall(match.group(1)):
        if value.startswith(("http://", "https://", "#")):
            continue
        target = (path.parent / value.split("#", 1)[0]).resolve()
        try:
            candidates.append(target.relative_to(root.resolve()).as_posix())
        except ValueError:
            continue
    return list(dict.fromkeys(candidates))[:24]


def _agent_index_concepts(root: Path, existing: set[str]) -> list[dict[str, Any]]:
    try:
        text = (root / "AGENTS.md").read_text(encoding="utf-8")
    except OSError:
        return []
    concepts: list[dict[str, Any]] = []
    for heading, body in _SECTION.findall(text):
        id_match = _ID.search(body)
        if not id_match:
            continue
        concept_id = id_match.group(1).strip()
        if concept_id in existing or not re.fullmatch(r"[a-z][a-z0-9-]+", concept_id):
            continue
        aliases = [concept_id, heading.strip()]
        what = _WHAT.search(body)
        if what:
            aliases.append(what.group(1).strip())
        links = [value.split("#", 1)[0] for value in _LINK.findall(body)]
        sources: list[dict[str, Any]] = []
        rank_by_role = {"state": 10, "adr": 20, "design": 30, "validation": 50}
        for index, path in enumerate(links):
            role = _role(path)
            sources.append(_source(concept_id, path, role, rank_by_role.get(role, 90) + index))
            if role == "state":
                for impl_index, implementation in enumerate(_extract_state_implementation_paths(root, path)):
                    impl_role = _role(implementation)
                    sources.append(_source(concept_id, implementation, impl_role, 40 + impl_index))
        if sources:
            concepts.append({
                "concept_id": concept_id,
                "subsystem_id": concept_id,
                "aliases": list(dict.fromkeys(aliases)),
                "sources": _deduplicate_sources(sources),
            })
    return concepts


def build_repository_route_inputs(
    root: Path,
    *,
    fact_scope: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    target = root.expanduser().resolve()
    inventory = load_operating_rules()
    concepts = _portable_concepts(inventory)
    concepts.extend(_agent_index_concepts(target, {item["concept_id"] for item in concepts}))
    registry = {
        "schema_version": 1,
        "registry_id": "orrery-agents-authority-route-index-v1",
        "registry_version": 1,
        "index_source": "AGENTS.md",
        "concepts": concepts,
    }
    observations: dict[str, Any] = {}
    phase0_path = target / "tests/fixtures/platform_neutral_phase0_baseline.json"
    published_skill_paths: set[str] | None = None
    try:
        phase0 = json.loads(phase0_path.read_text(encoding="utf-8"))
        published_skill_paths = set(phase0["published_release"]["skill_paths"])
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        published_skill_paths = None
    for concept in concepts:
        for source in concept["sources"]:
            path = target / source["path"]
            exists = path.is_file() or path.is_dir()
            claims: dict[str, Any] = {}
            if exists and source["role"] in {"state", "adr", "design"}:
                claims["semantic_decision"] = {
                    "status": "present", "fact_scope": fact_scope,
                    "reason_codes": ["indexed-governing-source-present"],
                }
            if exists and source["role"] == "implementation":
                claims["implementation"] = {
                    "status": "present", "fact_scope": fact_scope,
                    "reason_codes": ["implementation-path-present"],
                    "validation_status": "unknown",
                }
            if exists and source["role"] == "validation":
                claims["implementation"] = {
                    "status": "present", "fact_scope": fact_scope,
                    "reason_codes": ["validation-source-present"],
                    "validation_status": "present",
                }
            distribution_marker_present = exists
            if concept["concept_id"] == "authority-meta-model" and source["role"] in {"distribution", "consumer"}:
                if source["path"].endswith("SKILL.md"):
                    try:
                        distribution_marker_present = "orrery-operating-rules-v1" in path.read_text(encoding="utf-8")
                    except OSError:
                        distribution_marker_present = False
                elif source["path"].endswith("orrery-operating-rules-v1.json"):
                    distribution_marker_present = exists
            if distribution_marker_present and source["role"] in {"distribution", "consumer"}:
                claims["distribution_consumer"] = {
                    "status": "present", "fact_scope": fact_scope,
                    "reason_codes": ["consumer-projection-present-in-source-scope"],
                }
            if source["role"] == "release" and concept["concept_id"] == "authority-meta-model":
                published = (
                    published_skill_paths is not None
                    and "references/orrery-operating-rules-v1.json" in published_skill_paths
                )
                claims["public_default_release"] = {
                    "status": "present" if published else "absent" if published_skill_paths is not None else "unknown",
                    "fact_scope": "historical" if published_skill_paths is not None else "unknown",
                    "reason_codes": [
                        "published-v0.2.0-skill-includes-a4"
                        if published
                        else "published-v0.2.0-skill-excludes-a4"
                        if published_skill_paths is not None
                        else "published-release-inventory-unavailable"
                    ],
                    "negative_evidence": published_skill_paths is not None and not published,
                    "public_status": "present" if published else "absent" if published_skill_paths is not None else "unknown",
                    "default_status": "present" if published else "absent" if published_skill_paths is not None else "unknown",
                    "release_status": "present" if published else "absent" if published_skill_paths is not None else "unknown",
                }
            observations[source["source_id"]] = {
                "exists": exists,
                "link_valid": exists,
                "current": True,
                "claims": claims,
                "assertion_kind": "mechanical" if source["role"] not in {"template", "readme", "agent-assertion"} else "derived",
            }
    return registry, observations


def preflight_repository_query(
    root: Path,
    query: str,
    *,
    query_class: str | None = None,
    fact_scope: str = "unknown",
) -> dict[str, Any]:
    try:
        registry, observations = build_repository_route_inputs(root, fact_scope=fact_scope)
        return evaluate_authority_route(
            query=query,
            query_class=query_class,
            registry=registry,
            observations=observations,
        )
    except (AuthorityRouteError, OSError, ValueError) as exc:
        return unavailable_route_receipt(query, str(exc)[:400])


def _emit_human_inspect(value: dict[str, Any]) -> None:
    print(f"Operating rules: {value['status']}")
    print(f"Requested inventory version: {value['requested_inventory_version']}")
    print("Read-only: yes")
    if value["inventory"]:
        print(f"Rules: {len(value['inventory']['rules'])}")
        print(f"Inventory: {value['inventory']['inventory_id']}")
    else:
        print(f"Reason: {value['reason']}")


def _emit_human_route(value: dict[str, Any]) -> None:
    print("Authority Route Preflight: read-only")
    print("Concepts: " + (", ".join(value["selection"]["concept_ids"]) or "Unknown"))
    print("Query class: " + value["query"]["query_class"])
    for axis, claim in value["claim_dimensions"].items():
        print(f"{axis}: {claim['status']}")
    print("Absence claim: " + value["novelty_absence_gate"]["status"])


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.action == "inspect":
        command = "operating-rules-inspect"
        value = inspect_operating_rules(
            version=arguments.inventory_version,
            path=arguments.inventory_file,
        )
        if arguments.json_output:
            warnings = [] if value["status"] == "supported" else [issue("operating_rules_unavailable", value["reason"])]
            emit(response(command, status="ok" if not warnings else "warning", exit_code=JsonExitCode.OK, data=value, warnings=warnings))
        else:
            _emit_human_inspect(value)
        return int(JsonExitCode.OK)
    command = "authority-route-preflight"
    value = preflight_repository_query(
        arguments.target,
        arguments.query,
        query_class=arguments.query_class,
        fact_scope=arguments.fact_scope,
    )
    warnings = []
    if not value["selection"]["concept_ids"]:
        warnings.append(issue("authority_route_unknown", "concept could not be resolved; claims remain Unknown"))
    if arguments.json_output:
        emit(response(command, status="warning" if warnings else "ok", exit_code=JsonExitCode.OK, data=value, warnings=warnings))
    else:
        _emit_human_route(value)
    return int(JsonExitCode.OK)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_repository_route_inputs", "preflight_repository_query", "main"]
