"""Internal deterministic repository observations for Authority M2.1.

The collector parses authored Markdown into pre-normalized observations.  It
does not own Authority semantics: Core evaluates the observations.  The
contract remains an internal Candidate boundary until a later release gate.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from project_orrery_core.authority import (
    AUTHORITY_MODEL_VERSION,
    EVIDENCE_CAPABILITIES,
    evaluate_authority,
)


AUTHORITY_OBSERVATION_CONTRACT = "cli-authority-observations-v1"
ADR_FILE_RE = re.compile(r"^(\d{4}(?:\.\d+)?)-(.+)\.md$")
ADR_TOKEN_RE = re.compile(r"ADR-(\d{4}(?:\.\d+)?)")
META_RE = re.compile(r"^\s*-?\s*(?:\*\*)?([^:*：]+?)(?:\*\*)?\s*[:：]\s*(.*)$")
H2_RE = re.compile(r"^##\s+")
SKIPPED_FILENAMES = {"readme.md", "_template.md"}
ROLE_DIRECTORIES = (
    ("design", Path("docs") / "design"),
    ("plan", Path("docs") / "implementation" / "plans"),
    ("state", Path("docs") / "state"),
    ("validation", Path("docs") / "validation"),
    ("snapshot", Path("docs") / "snapshots"),
)
DEFAULT_EVIDENCE_VISIBILITY = (
    "revision-content",
    "human-or-agent-assertion",
)
EXPLICIT_VALIDATION_RESULTS = {
    "pass": "passed",
    "passed": "passed",
    "fail": "failed",
    "failed": "failed",
}

AuthorityEvaluator = Callable[
    [Mapping[str, Any], Sequence[Mapping[str, Any]]], dict[str, Any]
]


class AuthorityObservationParseError(ValueError):
    """Raised when authored metadata cannot be normalized safely."""


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _validate_source(root: Path, path: Path) -> None:
    if path.is_symlink():
        raise AuthorityObservationParseError(
            f"{_relative(root, path)}: authority source cannot be a symlink"
        )
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise AuthorityObservationParseError(
            f"{_relative(root, path)}: authority source escapes repository root"
        ) from exc


def _source_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _header_metadata(path: Path) -> dict[str, list[str]]:
    metadata: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if H2_RE.match(line):
            break
        match = META_RE.match(line)
        if match:
            metadata.setdefault(match.group(1).strip().casefold(), []).append(
                match.group(2).strip()
            )
    return metadata


def _single_metadata_value(
    metadata: Mapping[str, Sequence[str]], key: str, *, source: str
) -> str:
    values = list(metadata.get(key, ()))
    if len(values) > 1:
        raise AuthorityObservationParseError(
            f"{source}: duplicate {key.title()} metadata"
        )
    return values[0] if values else ""


def normalize_decision_lifecycle(status_raw: str) -> str:
    """Normalize only lifecycle values defined by Authority Model 1."""

    value = status_raw.strip().casefold()
    if "superseded by" in value or value.startswith("superseded"):
        return "superseded"
    if value.startswith("accepted"):
        return "accepted"
    if value.startswith("proposed"):
        return "proposed"
    if value.startswith("rejected"):
        return "rejected"
    if value.startswith("deprecated"):
        return "deprecated"
    if value.startswith("design") or value.startswith("deferred"):
        return "deferred"
    return "unknown"


def normalize_design_lifecycle(status_raw: str) -> str:
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
    values = list(metadata.get("result", ())) + list(metadata.get("outcome", ()))
    decisive = {
        EXPLICIT_VALIDATION_RESULTS[value.strip().casefold()]
        for value in values
        if value.strip().casefold() in EXPLICIT_VALIDATION_RESULTS
    }
    if len(decisive) > 1:
        raise AuthorityObservationParseError(
            f"{source}: conflicting explicit Result/Outcome metadata"
        )
    return next(iter(decisive), "unknown")


def _numbered_adr_paths(root: Path) -> list[Path]:
    decisions_dir = root / "docs" / "decisions"
    paths: list[Path] = []
    for path in sorted(decisions_dir.glob("*.md")):
        match = ADR_FILE_RE.match(path.name)
        if (
            path.is_file()
            and match
            and match.group(1) != "0000"
            and match.group(2).casefold() != "template"
        ):
            _validate_source(root, path)
            paths.append(path)
    return paths


def authority_source_paths(root: Path) -> list[Path]:
    """Return the exact authored sources visible to the M2.1 collector."""

    paths = _numbered_adr_paths(root)
    seed = root / "docs" / "core" / "principles.md"
    if seed.is_file():
        _validate_source(root, seed)
        paths.append(seed)
    for _, relative_directory in ROLE_DIRECTORIES:
        directory = root / relative_directory
        for path in sorted(directory.glob("*.md")):
            if path.is_file() and path.name.casefold() not in SKIPPED_FILENAMES:
                _validate_source(root, path)
                paths.append(path)
    return sorted(set(paths), key=lambda path: _relative(root, path))


def authority_observation_snapshot(root: Path) -> str:
    """Hash exact path/bytes pairs visible to the Candidate collector."""

    digest = hashlib.sha256()
    for path in authority_source_paths(root):
        digest.update(_relative(root, path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "cli-authority-observations:sha256:" + digest.hexdigest()


def _observation(
    *,
    kind: str,
    subject: str,
    source: str,
    source_sha256: str,
    evidence_category: str,
    **values: Any,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "subject": subject,
        **values,
        "evidence_category": evidence_category,
        "source": source,
        "source_sha256": source_sha256,
    }


def _decision_documents(
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    documents: list[dict[str, Any]] = []
    by_subject: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, str]] = []

    for path in _numbered_adr_paths(root):
        match = ADR_FILE_RE.match(path.name)
        assert match is not None
        subject = "ADR-" + match.group(1)
        source = _relative(root, path)
        digest = _source_sha256(path)
        metadata = _header_metadata(path)
        status_raw = _single_metadata_value(metadata, "status", source=source)
        observation = _observation(
            kind="decision",
            subject=subject,
            source=source,
            source_sha256=digest,
            evidence_category="revision-content",
            id=subject,
            status=normalize_decision_lifecycle(status_raw),
        )
        for relation in ("amends", "supersedes"):
            values = list(metadata.get(relation, ()))
            targets = sorted(
                {
                    "ADR-" + token
                    for value in values
                    for token in ADR_TOKEN_RE.findall(value)
                }
            )
            if values and not targets:
                raise AuthorityObservationParseError(
                    f"{source}: explicit {relation.title()} metadata has no ADR target"
                )
            if subject in targets:
                raise AuthorityObservationParseError(
                    f"{source}: {relation} cannot target {subject} itself"
                )
            if targets:
                observation[relation] = targets
        document = {
            "source": source,
            "source_sha256": digest,
            "role": "adr",
            "subject": subject,
            "metadata": {"status_raw": status_raw},
            "observations": [observation],
        }
        if subject in by_subject:
            raise AuthorityObservationParseError(
                f"{source}: duplicate decision id {subject}"
            )
        documents.append(document)
        by_subject[subject] = document

    for document in documents:
        observation = document["observations"][0]
        status_raw = document["metadata"]["status_raw"]
        if "superseded by" not in status_raw.casefold():
            continue
        replacements = sorted(
            {"ADR-" + token for token in ADR_TOKEN_RE.findall(status_raw)}
        )
        if not replacements:
            raise AuthorityObservationParseError(
                f"{document['source']}: Superseded by status has no ADR target"
            )
        for replacement in replacements:
            replacement_document = by_subject.get(replacement)
            if replacement_document is None:
                unresolved.append(
                    {
                        "source": replacement,
                        "relation": "supersedes",
                        "target": str(document["subject"]),
                        "reason": "replacement-not-visible",
                    }
                )
                continue
            replacement_observation = replacement_document["observations"][0]
            targets = replacement_observation.setdefault("supersedes", [])
            if document["subject"] not in targets:
                targets.append(document["subject"])
                targets.sort()

    visible = set(by_subject)
    for document in documents:
        observation = document["observations"][0]
        for relation in ("amends", "supersedes"):
            for target in observation.get(relation, []):
                if target not in visible:
                    unresolved.append(
                        {
                            "source": str(document["subject"]),
                            "relation": relation,
                            "target": target,
                            "reason": "target-not-visible",
                        }
                    )
    unresolved.sort(
        key=lambda item: (
            item["source"],
            item["relation"],
            item["target"],
            item["reason"],
        )
    )
    return documents, unresolved


def _role_for_path(root: Path, path: Path) -> str:
    if path == root / "docs" / "core" / "principles.md":
        return "seed"
    relative = path.relative_to(root)
    for role, directory in ROLE_DIRECTORIES:
        try:
            relative.relative_to(directory)
        except ValueError:
            continue
        return role
    raise AuthorityObservationParseError(
        f"{_relative(root, path)}: unsupported authority source location"
    )


def _role_document(root: Path, path: Path) -> dict[str, Any]:
    role = _role_for_path(root, path)
    source = _relative(root, path)
    digest = _source_sha256(path)
    metadata = _header_metadata(path)
    status_raw = _single_metadata_value(metadata, "status", source=source)
    subject = source

    if role == "seed":
        observation = _observation(
            kind="seed",
            subject=subject,
            source=source,
            source_sha256=digest,
            evidence_category="revision-content",
            present=True,
        )
    elif role == "design":
        observation = _observation(
            kind="design",
            subject=subject,
            source=source,
            source_sha256=digest,
            evidence_category="revision-content",
            lifecycle=normalize_design_lifecycle(status_raw),
        )
    elif role == "plan":
        observation = _observation(
            kind="plan",
            subject=subject,
            source=source,
            source_sha256=digest,
            evidence_category="revision-content",
            planned=True,
        )
    elif role == "state":
        observation = _observation(
            kind="state",
            subject=subject,
            source=source,
            source_sha256=digest,
            evidence_category="revision-content",
            current=True,
        )
    elif role == "validation":
        result = normalize_validation_result(metadata, source=source)
        observation = _observation(
            kind="validation",
            subject=subject,
            source=source,
            source_sha256=digest,
            evidence_category=(
                "human-or-agent-assertion"
                if result in {"passed", "failed"}
                else "revision-content"
            ),
            result=result,
        )
    else:
        observation = _observation(
            kind="snapshot",
            subject=subject,
            source=source,
            source_sha256=digest,
            evidence_category="revision-content",
            live_state=False,
        )

    return {
        "source": source,
        "source_sha256": digest,
        "role": role,
        "subject": subject,
        "metadata": {"status_raw": status_raw},
        "observations": [observation],
    }


def collect_authority_documents(
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    decisions, unresolved = _decision_documents(root)
    decision_sources = {document["source"] for document in decisions}
    documents = list(decisions)
    for path in authority_source_paths(root):
        if _relative(root, path) not in decision_sources:
            documents.append(_role_document(root, path))
    documents.sort(key=lambda document: str(document["source"]))
    return documents, unresolved


def _individual_observations(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    observations = [dict(item) for item in document["observations"]]
    if document["role"] == "adr":
        observation = observations[0]
        observation.pop("id", None)
        observation.pop("amends", None)
        observation.pop("supersedes", None)
    return observations


def _evidence_provenance(
    observations: Sequence[Mapping[str, Any]], visibility: Sequence[str]
) -> list[dict[str, Any]]:
    visible = set(visibility)
    return [
        {
            "subject": observation.get("subject"),
            "source": observation.get("source"),
            "source_sha256": observation.get("source_sha256"),
            "kind": observation.get("kind"),
            "category": observation.get("evidence_category"),
            "capability": EVIDENCE_CAPABILITIES.get(
                str(observation.get("evidence_category"))
            ),
            "visible": observation.get("evidence_category") in visible,
        }
        for observation in observations
        if observation.get("evidence_category") is not None
    ]


def build_cli_authority_contract(
    root: Path,
    *,
    evaluator: AuthorityEvaluator = evaluate_authority,
    authority_model_version: str = AUTHORITY_MODEL_VERSION,
    fact_scope: str = "unknown",
    evidence_visibility: Sequence[str] = DEFAULT_EVIDENCE_VISIBILITY,
) -> dict[str, Any]:
    """Build the internal M2.1 repository observation/claim bundle."""

    repository_snapshot = authority_observation_snapshot(root)
    conformance_input = {
        "authority_model_version": authority_model_version,
        "repository_snapshot": repository_snapshot,
        "fact_scope": fact_scope,
        "evidence_visibility": list(evidence_visibility),
    }
    documents, unresolved = collect_authority_documents(root)
    for document in documents:
        observations = _individual_observations(document)
        result = evaluator(conformance_input, observations)
        document["claims"] = result["claims"]
        document["relations"] = result["relations"]
        document["must_not_infer"] = result["must_not_infer"]
        document["evidence_provenance"] = _evidence_provenance(
            document["observations"], evidence_visibility
        )

    decision_observations = [
        document["observations"][0]
        for document in documents
        if document["role"] == "adr"
    ]
    if unresolved:
        decision_graph = {
            "status": "unknown",
            "reason": "unresolved-explicit-relation",
            "result": None,
        }
    else:
        decision_graph = {
            "status": "evaluated",
            "reason": None,
            "result": evaluator(conformance_input, decision_observations),
        }

    return {
        "contract_version": AUTHORITY_OBSERVATION_CONTRACT,
        "mode": "candidate-shadow",
        "production_behavior_switched": False,
        "conformance_input": conformance_input,
        "documents": documents,
        "decision_graph": decision_graph,
        "unresolved_relations": unresolved,
        "semantic_limits": {
            "implementation": "not-inferred-from-state-prose-or-document-presence",
            "validation": "reported-result-is-an-assertion-without-executable-evidence",
            "references": "predecessor-body-and-state-references-are-non-normative",
        },
    }
