"""Observatory parser to Core Authority shadow comparison.

The legacy docsite parser remains the production source for navigation,
badges, graphs, statistics, and rendered HTML. This internal adapter compares
its normalized ADR lifecycle output with an injected Core evaluator without
changing or exporting Observatory behavior.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any


AuthorityEvaluator = Callable[
    [Mapping[str, Any], Sequence[Mapping[str, Any]]], dict[str, Any]
]
ADR_FILE_RE = re.compile(r"^(\d{4}(?:\.\d+)?)-(.+)\.md$")
ADR_TOKEN_RE = re.compile(r"ADR-(\d{4}(?:\.\d+)?)")
RELATION_META_RE = re.compile(
    r"^\s*-?\s*(?:\*\*)?(Amends|Supersedes)(?:\*\*)?\s*[:：]\s*(.*)$",
    re.IGNORECASE,
)


class AuthorityRelationParseError(ValueError):
    """Raised when explicit ADR relation metadata cannot be normalized."""


def authority_input_snapshot(decisions_dir: Path) -> str:
    """Hash every numbered ADR byte visible to the legacy parser."""

    digest = hashlib.sha256()
    for path in sorted(decisions_dir.glob("*.md")):
        match = ADR_FILE_RE.match(path.name)
        if (
            not path.is_file()
            or not match
            or match.group(1) == "0000"
            or match.group(2) == "template"
        ):
            continue
        relative = path.relative_to(decisions_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "observatory-adr-inputs:sha256:" + digest.hexdigest()


def normalize_decision_status(status_raw: str) -> str:
    """Normalize raw ADR metadata independently from the legacy classifier."""

    value = status_raw.strip().lower()
    if value.startswith("superseded"):
        return "superseded"
    if value.startswith("deprecated"):
        return "deprecated"
    if value.startswith("proposed"):
        return "proposed"
    if value.startswith("design"):
        return "deferred"
    if value.startswith("accepted"):
        return "superseded" if "superseded" in value else "accepted"
    return "other"


def _decision_id(number: Any) -> str:
    return "ADR-" + str(number)


def _relation_metadata(path: Path) -> dict[str, list[str]]:
    """Read only explicit Amends/Supersedes metadata from an ADR header."""

    relations: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            break
        match = RELATION_META_RE.match(line)
        if not match:
            continue
        relation = match.group(1).lower()
        targets = [_decision_id(number) for number in ADR_TOKEN_RE.findall(match.group(2))]
        if not targets:
            raise AuthorityRelationParseError(
                f"{path.name}: explicit {match.group(1)} metadata has no ADR target"
            )
        relations[relation] = sorted(set(relations.get(relation, []) + targets))
    return relations


def collect_decision_observations(
    adrs: Sequence[Mapping[str, Any]], decisions_dir: Path
) -> dict[str, Any]:
    """Normalize explicit ADR lifecycle and relation observations.

    ``Predecessor``, ordinary Markdown references, and State references are
    deliberately excluded. ``Status: Superseded by ADR-N`` is inverted into
    the normative ``ADR-N supersedes current ADR`` direction.
    """

    observations: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    explicit_sources: list[dict[str, str]] = []
    unresolved_targets: list[dict[str, str]] = []
    legacy_superseded_by: dict[str, list[str]] = {}

    for adr in adrs:
        decision_id = _decision_id(adr.get("num", "unknown"))
        observation = {
            "kind": "decision",
            "id": decision_id,
            "status": normalize_decision_status(str(adr.get("status_raw", ""))),
            "evidence_category": "revision-content",
        }
        source_file = decisions_dir / str(adr.get("file", ""))
        for relation, targets in _relation_metadata(source_file).items():
            if decision_id in targets:
                raise AuthorityRelationParseError(
                    f"{source_file.name}: {relation} cannot target {decision_id} itself"
                )
            observation[relation] = targets
            for target in targets:
                explicit_sources.append(
                    {
                        "source": decision_id,
                        "relation": relation,
                        "target": target,
                        "encoding": "explicit-header",
                    }
                )
        observations.append(observation)
        by_id[decision_id] = observation

    for adr in adrs:
        decision_id = _decision_id(adr.get("num", "unknown"))
        status_raw = str(adr.get("status_raw", ""))
        if "superseded by" not in status_raw.lower():
            continue
        replacements = [_decision_id(number) for number in ADR_TOKEN_RE.findall(status_raw)]
        legacy_superseded_by[decision_id] = sorted(set(replacements))
        for replacement in replacements:
            replacement_observation = by_id.get(replacement)
            if replacement_observation is None:
                unresolved_targets.append(
                    {
                        "source": replacement,
                        "relation": "supersedes",
                        "target": decision_id,
                        "reason": "replacement-not-visible",
                    }
                )
                continue
            targets = replacement_observation.setdefault("supersedes", [])
            if decision_id not in targets:
                targets.append(decision_id)
                targets.sort()
            explicit_sources.append(
                {
                    "source": replacement,
                    "relation": "supersedes",
                    "target": decision_id,
                    "encoding": "status-superseded-by",
                }
            )

    visible_ids = set(by_id)
    for observation in observations:
        source = str(observation["id"])
        for relation in ("supersedes", "amends"):
            for target in observation.get(relation, []):
                if target not in visible_ids:
                    unresolved_targets.append(
                        {
                            "source": source,
                            "relation": relation,
                            "target": target,
                            "reason": "target-not-visible",
                        }
                    )

    return {
        "observations": observations,
        "sources": explicit_sources,
        "unresolved_targets": unresolved_targets,
        "legacy_superseded_by": legacy_superseded_by,
    }


def _expected_relations(observations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected: dict[str, Any] = {}
    for observation in observations:
        relations = {
            relation: list(observation[relation])
            for relation in ("supersedes", "amends")
            if observation.get(relation)
        }
        if relations:
            expected[str(observation["id"])] = relations
    return expected


def build_observatory_authority_shadow(
    adrs: Sequence[Mapping[str, Any]],
    decisions_dir: Path,
    *,
    evaluator: AuthorityEvaluator,
    authority_model_version: str,
    fact_scope: str = "unknown",
) -> dict[str, Any]:
    """Compare legacy ADR lifecycle classes with the Core evaluator.

    The caller supplies the internal Core evaluator so this experimental
    module does not create a public package dependency or stable API promise.
    """

    conformance_input = {
        "authority_model_version": authority_model_version,
        "repository_snapshot": authority_input_snapshot(decisions_dir),
        "fact_scope": fact_scope,
        "evidence_visibility": ["revision-content"],
    }
    comparisons: list[dict[str, Any]] = []
    differences: list[dict[str, Any]] = []

    for adr in adrs:
        number = str(adr.get("num", "unknown"))
        legacy_status = str(adr.get("status_class", "other"))
        normalized_status = normalize_decision_status(str(adr.get("status_raw", "")))
        core = evaluator(
            conformance_input,
            [
                {
                    "kind": "decision",
                    "status": normalized_status,
                    "evidence_category": "revision-content",
                }
            ],
        )
        core_status = core["claims"].get("decision_status", "unknown")
        comparison = {
            "adr": "ADR-" + number,
            "legacy": legacy_status,
            "core": core_status,
            "status": "match" if legacy_status == core_status else "mismatch",
        }
        comparisons.append(comparison)
        if legacy_status != core_status:
            differences.append(
                {
                    "adr": "ADR-" + number,
                    "field": "decision_status",
                    "legacy": legacy_status,
                    "core": core_status,
                    "category": "parser-gap",
                }
            )

    relation_input = collect_decision_observations(adrs, decisions_dir)
    relation_result = evaluator(conformance_input, relation_input["observations"])
    expected_relations = _expected_relations(relation_input["observations"])
    core_relations = relation_result["relations"]
    if core_relations != expected_relations:
        differences.append(
            {
                "field": "relations",
                "expected": expected_relations,
                "core": core_relations,
                "category": "relation-evaluator-gap",
            }
        )

    effective_claims = {
        key: relation_result["claims"][key]
        for key in ("effective_decision", "effective_decisions")
        if key in relation_result["claims"]
    }
    relation_status = "match"
    if core_relations != expected_relations:
        relation_status = "mismatch"
    elif relation_input["unresolved_targets"]:
        relation_status = "unknown"

    comparison_status = "mismatch" if differences else relation_status

    return {
        "mode": "shadow",
        "production_authority": "legacy-observatory-parser",
        "production_behavior_switched": False,
        "conformance_input": conformance_input,
        "comparison": {
            "status": comparison_status,
            "checked": len(comparisons),
            "items": comparisons,
            "differences": differences,
            "relation_contract": {
                "source": "explicit-adr-metadata",
                "status": relation_status,
                "observations": relation_input["observations"],
                "sources": relation_input["sources"],
                "unresolved_targets": relation_input["unresolved_targets"],
                "expected_relations": expected_relations,
                "core_relations": core_relations,
                "effective_claims": effective_claims,
                "legacy_superseded_by": relation_input["legacy_superseded_by"],
            },
            "legacy_only": {
                "predecessors": "legacy-graph-heuristic",
                "refs": "legacy-reference-graph",
                "state_refs": "legacy-reference-graph",
            },
        },
    }
