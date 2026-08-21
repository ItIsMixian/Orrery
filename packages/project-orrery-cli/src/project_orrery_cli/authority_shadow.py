"""Legacy CLI to Core Authority shadow comparison.

The legacy validator remains the production decision path. This module
normalizes only the legacy Accepted-ADR observation and compares it with the
experimental Core evaluator without switching exit codes or authority status.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from project_orrery_core.authority import AUTHORITY_MODEL_VERSION, evaluate_authority

from .authority_observations import build_cli_authority_contract


@dataclass(frozen=True)
class LegacyAuthorityFacts:
    accepted_adr: bool
    entrance_mapped: bool
    pending_marker: bool
    integrated: bool


def _read_optional_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _accepted_adr_paths(root: Path) -> list[Path]:
    decision_root = root / "docs" / "decisions"
    paths: list[Path] = []
    for path in sorted(decision_root.glob("[0-9][0-9][0-9][0-9]-*.md")):
        if path.name.startswith("0000-"):
            continue
        if re.search(
            r"(?im)^Status\s*:\s*Accepted\b", path.read_text(encoding="utf-8")
        ):
            paths.append(path)
    return paths


def scan_legacy_authority(root: Path) -> LegacyAuthorityFacts:
    """Preserve the validator's pre-shadow authority heuristic exactly."""

    agents_text = _read_optional_text(root / "AGENTS.md")
    progress_text = _read_optional_text(root / "docs" / "PROGRESS.md")
    accepted_adr = bool(_accepted_adr_paths(root))
    entrance_mapped = all(
        token in agents_text
        for token in ("docs/HANDOFF.md", "docs/PROGRESS.md", "docs/state/")
    )
    pending_marker = (
        "migration pending" in progress_text.lower() or "迁移待" in progress_text
    )
    return LegacyAuthorityFacts(
        accepted_adr=accepted_adr,
        entrance_mapped=entrance_mapped,
        pending_marker=pending_marker,
        integrated=accepted_adr and entrance_mapped and not pending_marker,
    )


def authority_input_snapshot(root: Path) -> str:
    """Hash the exact files visible to the current legacy authority scan."""

    candidates = [root / "AGENTS.md", root / "docs" / "PROGRESS.md"]
    candidates.extend(
        sorted((root / "docs" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md"))
    )
    digest = hashlib.sha256()
    for path in candidates:
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(root).as_posix()
            content = path.read_bytes()
        except (OSError, ValueError):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return "authority-inputs:sha256:" + digest.hexdigest()


def build_authority_shadow(
    root: Path,
    legacy: LegacyAuthorityFacts | None = None,
    *,
    fact_scope: str = "unknown",
) -> dict[str, Any]:
    """Return a no-switch shadow report for the legacy CLI authority heuristic."""

    current = legacy or scan_legacy_authority(root)
    conformance_input = {
        "authority_model_version": AUTHORITY_MODEL_VERSION,
        "repository_snapshot": authority_input_snapshot(root),
        "fact_scope": fact_scope,
        "evidence_visibility": ["revision-content"],
    }
    observations = [
        {
            "kind": "decision",
            "status": "accepted" if _accepted_adr_paths(root) else "absent",
            "evidence_category": "revision-content",
        }
    ]
    core = evaluate_authority(conformance_input, observations)
    candidate_contract = build_cli_authority_contract(root, fact_scope=fact_scope)
    core_accepted = core["claims"].get("decision_status") == "accepted"
    differences: list[dict[str, Any]] = []
    if current.accepted_adr != core_accepted:
        differences.append(
            {
                "field": "accepted_adr",
                "legacy": current.accepted_adr,
                "core": core_accepted,
                "category": "parser-gap",
            }
        )

    return {
        "mode": "shadow",
        "production_authority": "legacy-cli",
        "production_behavior_switched": False,
        "legacy": asdict(current),
        "core": core,
        "candidate_contract": candidate_contract,
        "comparison": {
            "status": "match" if not differences else "mismatch",
            "differences": differences,
            "legacy_only": {
                "entrance_mapped": "legacy-adoption-heuristic",
                "pending_marker": "legacy-adoption-heuristic",
                "integrated": "legacy-adoption-heuristic",
            },
        },
    }
