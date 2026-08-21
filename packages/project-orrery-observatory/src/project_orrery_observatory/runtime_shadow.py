"""Internal runtime bridge for legacy rendering plus Authority shadow reports.

This bridge is deliberately not wired into the managed ``build_docsite.py``
or ``serve.py`` entrypoints.  It lets the self-hosted repository dual-run the
real legacy renderer and the Candidate Core evaluator while proving that the
production HTML and statistics are returned unchanged.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .authority_role_shadow import build_observatory_role_shadow
from .authority_shadow import build_observatory_authority_shadow
from .authority_model_status import project_authority_model_status


AuthorityEvaluator = Callable[
    [Mapping[str, Any], Sequence[Mapping[str, Any]]], dict[str, Any]
]
LegacyRenderer = Callable[[Path, Path, Path, str], tuple[str, Mapping[str, Any]]]
LegacyAdrParser = Callable[[Path], Sequence[Mapping[str, Any]]]


class AuthorityModelUnavailableError(RuntimeError):
    """Internal fail-closed signal that remains isolated from legacy render."""


def _overall_status(adr_status: str, role_status: str) -> str:
    if "mismatch" in (adr_status, role_status):
        return "mismatch"
    if "unknown" in (adr_status, role_status):
        return "unknown"
    return "match"


def render_with_authority_shadow(
    docs_dir: Path,
    agents_file: Path,
    root: Path,
    title: str,
    *,
    legacy_renderer: LegacyRenderer,
    legacy_adr_parser: LegacyAdrParser,
    evaluator: AuthorityEvaluator,
    authority_model_version: str,
    fact_scope: str = "unknown",
    authority_model_capability: Mapping[str, Any] | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Return the untouched legacy output plus a warning-only shadow report.

    Legacy rendering errors still propagate because no production output
    exists in that case.  Authority shadow errors are isolated into the report
    so an experimental parser/evaluator cannot break the legacy reader.
    """

    page, raw_stats = legacy_renderer(docs_dir, agents_file, root, title)
    stats = dict(raw_stats)
    production = {
        "html_sha256": hashlib.sha256(page.encode("utf-8")).hexdigest(),
        "stats": dict(stats),
    }
    model_status = project_authority_model_status(authority_model_capability)

    try:
        if model_status["read_only"]:
            raise AuthorityModelUnavailableError(
                "deterministic Authority shadow disabled by fail-closed model capability"
            )
        adrs = legacy_adr_parser(docs_dir / "decisions")
        adr_report = build_observatory_authority_shadow(
            adrs,
            docs_dir / "decisions",
            evaluator=evaluator,
            authority_model_version=authority_model_version,
            fact_scope=fact_scope,
        )
        role_report = build_observatory_role_shadow(
            docs_dir,
            evaluator=evaluator,
            authority_model_version=authority_model_version,
            fact_scope=fact_scope,
        )
        adr_status = str(adr_report["comparison"]["status"])
        role_status = (
            "match"
            if role_report["role_contract"]["status"] == "observed"
            else str(role_report["role_contract"]["status"])
        )
        shadow: dict[str, Any] = {
            "status": _overall_status(adr_status, role_status),
            "authority_model_version": authority_model_version,
            "fact_scope": fact_scope,
            "adr": adr_report,
            "roles": role_report,
        }
    except Exception as error:  # shadow failures must not break legacy rendering
        shadow = {
            "status": "unavailable",
            "authority_model_version": authority_model_version,
            "fact_scope": fact_scope,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
        }

    report = {
        "mode": "shadow",
        "production_authority": "legacy-observatory-renderer",
        "production_behavior_switched": False,
        "production": production,
        "authority_model": model_status,
        "shadow": shadow,
    }
    return page, stats, report
