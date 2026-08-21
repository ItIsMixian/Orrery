"""Internal Observatory shadow adapter for non-ADR authority roles.

The production docsite still classifies documents by directory and renders
their Markdown directly.  This module adds a fail-closed, package-level
comparison boundary for Design, Plan, State, and Validation without changing
the build/serve path or exposing a public Observatory API.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any


AuthorityEvaluator = Callable[
    [Mapping[str, Any], Sequence[Mapping[str, Any]]], dict[str, Any]
]
META_RE = re.compile(r"^\s*-?\s*(?:\*\*)?([^:*：]+?)(?:\*\*)?\s*[:：]\s*(.*)$")
H2_RE = re.compile(r"^##\s+")
EXPLICIT_VALIDATION_RESULTS = {
    "pass": "passed",
    "passed": "passed",
    "fail": "failed",
    "failed": "failed",
}
ROLE_LOCATIONS = (
    ("design", "design", Path("design")),
    ("plan", "implementation", Path("implementation") / "plans"),
    ("state", "state", Path("state")),
    ("validation", "validation", Path("validation")),
)
SKIPPED_FILENAMES = {"readme.md", "_template.md"}


class AuthorityRoleParseError(ValueError):
    """Raised when explicit authority-role metadata is contradictory."""


def _role_paths(docs_dir: Path) -> list[tuple[str, str, Path]]:
    paths: list[tuple[str, str, Path]] = []
    for role, legacy_family, relative_dir in ROLE_LOCATIONS:
        directory = docs_dir / relative_dir
        for path in sorted(directory.glob("*.md")):
            if path.is_file() and path.name.lower() not in SKIPPED_FILENAMES:
                paths.append((role, legacy_family, path))
    return paths


def authority_role_input_snapshot(docs_dir: Path) -> str:
    """Hash exactly the role documents visible to this shadow collector."""

    digest = hashlib.sha256()
    for _, _, path in _role_paths(docs_dir):
        relative = path.relative_to(docs_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "observatory-authority-role-inputs:sha256:" + digest.hexdigest()


def _header_metadata(path: Path) -> dict[str, list[str]]:
    metadata: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if H2_RE.match(line):
            break
        match = META_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip().casefold()
        metadata.setdefault(key, []).append(match.group(2).strip())
    return metadata


def _single_metadata_value(
    metadata: Mapping[str, Sequence[str]], key: str, *, source: str
) -> str:
    values = list(metadata.get(key, ()))
    if len(values) > 1:
        raise AuthorityRoleParseError(f"{source}: duplicate {key.title()} metadata")
    return values[0] if values else ""


def normalize_design_lifecycle(status_raw: str) -> str:
    """Normalize only Design lifecycle terms defined by the Meta Model."""

    value = status_raw.strip().casefold()
    for prefix, lifecycle in (
        ("approved", "approved"),
        ("draft", "draft"),
        ("deprecated", "deprecated"),
    ):
        if value == prefix or value.startswith(prefix + " "):
            return lifecycle
    return "unknown"


def normalize_validation_result(
    metadata: Mapping[str, Sequence[str]], *, source: str
) -> str:
    """Return a result only for an explicit, unambiguous Result/Outcome value.

    Existing free-form validation prose and Status metadata deliberately stay
    Unknown.  The shadow parser does not infer success from words such as
    "verified", from document presence, or from a filename.
    """

    raw_values = list(metadata.get("result", ())) + list(metadata.get("outcome", ()))
    decisive = {
        EXPLICIT_VALIDATION_RESULTS[value.strip().casefold()]
        for value in raw_values
        if value.strip().casefold() in EXPLICIT_VALIDATION_RESULTS
    }
    if len(decisive) > 1:
        raise AuthorityRoleParseError(
            f"{source}: conflicting explicit Result/Outcome metadata"
        )
    return next(iter(decisive), "unknown")


def collect_authority_role_observations(docs_dir: Path) -> list[dict[str, Any]]:
    """Collect deterministic observations for four non-ADR authority roles."""

    collected: list[dict[str, Any]] = []
    for role, legacy_family, path in _role_paths(docs_dir):
        source = path.relative_to(docs_dir.parent).as_posix()
        metadata = _header_metadata(path)
        status_raw = _single_metadata_value(metadata, "status", source=source)

        if role == "design":
            lifecycle = normalize_design_lifecycle(status_raw)
            observation = {
                "kind": "design",
                "lifecycle": lifecycle,
                "evidence_category": "revision-content",
            }
        elif role == "plan":
            observation = {
                "kind": "plan",
                "planned": True,
                "evidence_category": "revision-content",
            }
        elif role == "state":
            observation = {
                "kind": "state",
                "current": True,
                "evidence_category": "revision-content",
            }
        else:
            result = normalize_validation_result(metadata, source=source)
            observation = {
                "kind": "validation",
                "result": result,
                "evidence_category": (
                    "reproducible-executable-validation"
                    if result in {"passed", "failed"}
                    else "revision-content"
                ),
            }

        collected.append(
            {
                "source": source,
                "role": role,
                "legacy_family": legacy_family,
                "status_raw": status_raw,
                "observation": observation,
            }
        )
    return collected


def build_observatory_role_shadow(
    docs_dir: Path,
    *,
    evaluator: AuthorityEvaluator,
    authority_model_version: str,
    fact_scope: str = "unknown",
    evidence_visibility: Sequence[str] = (
        "revision-content",
        "reproducible-executable-validation",
    ),
) -> dict[str, Any]:
    """Evaluate role observations without changing Observatory production behavior."""

    conformance_input = {
        "authority_model_version": authority_model_version,
        "repository_snapshot": authority_role_input_snapshot(docs_dir),
        "fact_scope": fact_scope,
        "evidence_visibility": list(evidence_visibility),
    }
    documents = collect_authority_role_observations(docs_dir)
    for document in documents:
        result = evaluator(conformance_input, [document["observation"]])
        document["claims"] = result["claims"]
        document["must_not_infer"] = result["must_not_infer"]

    counts = Counter(document["role"] for document in documents)
    validation_unknown = sum(
        document["claims"].get("validation_evidence") == "unknown"
        for document in documents
        if document["role"] == "validation"
    )
    return {
        "mode": "shadow",
        "production_authority": "legacy-docsite-family-parser",
        "production_behavior_switched": False,
        "conformance_input": conformance_input,
        "role_contract": {
            "status": "observed",
            "counts": dict(sorted(counts.items())),
            "validation_unknown": validation_unknown,
            "documents": documents,
            "semantic_limits": {
                "plan": "planned-does-not-imply-current-or-implemented",
                "state": "current-role-does-not-prove-implementation",
                "validation": "document-presence-and-free-form-status-remain-unknown",
            },
        },
    }
