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

    return {
        "mode": "shadow",
        "production_authority": "legacy-observatory-parser",
        "production_behavior_switched": False,
        "conformance_input": conformance_input,
        "comparison": {
            "status": "match" if not differences else "mismatch",
            "checked": len(comparisons),
            "items": comparisons,
            "differences": differences,
            "legacy_only": {
                "predecessors": "legacy-graph-heuristic",
                "supersedes": "legacy-graph-heuristic",
                "refs": "legacy-reference-graph",
                "state_refs": "legacy-reference-graph",
            },
        },
    }
