"""Read-only Personal Observatory projection over canonical collaboration data.

The collector deliberately delegates Git identity, Scope, finding, lifecycle,
review, integration, inventory, and cleanup semantics to ``project_orrery_core``.
This module only aggregates those machine contracts for presentation; it does
not mutate Workstream sessions or infer W3 decisions.
"""

from __future__ import annotations

import html
import json
import os
import stat
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .display_vocabulary import (
    TECHNICAL_DETAILS_LABEL,
    display_status,
    maintenance_reason,
    workspace_classification,
)


PROJECTION_SCHEMA = "project-orrery-personal-observatory-v1"
W3_SLOT_KEYS = ("review_queue", "integration_eligibility", "cleanup_eligibility")
W3_PROJECTION_SCHEMA_VERSION = 1
DELIVERY_PHASES = {"created", "investigating", "implementing", "validating", "review-ready"}


class _W3ProviderIncompatible(ValueError):
    pass


def _now(value: str | None = None) -> str:
    return value or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _short_oid(value: object) -> str:
    text = str(value or "")
    return text[:9] if text else "Unknown"


def _branch_label(value: object) -> str:
    text = str(value or "")
    return text.removeprefix("refs/heads/") if text else "detached"


def _w3_slots(projection: Mapping[str, Any] | None) -> dict[str, dict[str, str]]:
    """Consume display-ready W3 slots without implementing any W3 policy."""

    if projection is None:
        return {
            key: {
                "status": "unavailable",
                "label": "Unavailable",
                "detail": "W3 provider unavailable or incompatible · Unknown",
                "source": "optional-w3-slot",
            }
            for key in W3_SLOT_KEYS
        }
    slots: dict[str, dict[str, str]] = {}
    for key in W3_SLOT_KEYS:
        value = projection.get(key)
        if not isinstance(value, Mapping):
            slots[key] = {
                "status": "unavailable",
                "label": "Unavailable",
                "detail": "W3 slot missing",
                "source": "optional-w3-slot",
            }
            continue
        slots[key] = {
            "status": str(value.get("status", "unknown")),
            "label": str(value.get("label", "Unknown")),
            "detail": str(value.get("detail", "W3 provider supplied no detail")),
            "source": str(value.get("source", "w3-display-provider")),
        }
    return slots


def _require_schema(bundle: Mapping[str, Any], key: str, expected: int) -> None:
    if bundle.get(key) != expected:
        raise _W3ProviderIncompatible(f"unsupported W3 {key}: {bundle.get(key)!r}")


def _read_contained_json(path: Path, boundary: Path, description: str) -> dict[str, Any]:
    try:
        resolved_boundary = boundary.resolve(strict=True)
        resolved = path.resolve(strict=True)
        resolved.relative_to(resolved_boundary)
        metadata = path.lstat()
    except (OSError, ValueError) as error:
        raise ValueError(f"cannot safely inspect {description}: {error}") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"{description} must be a regular file inside its W3 bundle")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {description}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{description} must contain a JSON object")
    return value


def _load_closure_receipt_bundles(
    inventory_entries: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Follow W3 closure paths/log refs without importing Core-private helpers."""

    from project_orrery_core.collaboration import validate_collaboration_contract

    closures: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in inventory_entries:
        summary = entry.get("closure", {})
        closure_id = str(summary.get("closure_id") or "")
        record_path = summary.get("record_path")
        if not closure_id or closure_id in seen:
            continue
        if not isinstance(record_path, str) or not record_path:
            raise ValueError("W3 closure summary is missing its stable record_path")
        seen.add(closure_id)
        closure_path = Path(record_path)
        if closure_path.name != f"{closure_id}.json":
            raise ValueError("W3 closure record_path does not match its closure ID")
        closure = _read_contained_json(
            closure_path, closure_path.parent, "closure record"
        )
        validate_collaboration_contract(closure)
        if closure.get("contract_type") != "closure-record" or closure.get(
            "closure_id"
        ) != closure_id:
            raise ValueError("W3 closure record does not match its inventory summary")
        if summary.get("review_package_id") != closure.get("review_package_id"):
            raise ValueError("W3 closure review-package binding does not match inventory")
        expected_log_ref = f"git-private:orrery/closures/actions/{closure_id}/"
        if closure.get("cleanup_action_log_ref") != expected_log_ref:
            raise ValueError("W3 closure cleanup_action_log_ref is incompatible")
        closures.append({**closure, "record_path": str(closure_path)})

        actions_root = closure_path.parent / "actions"
        directory = actions_root / closure_id
        if not directory.is_dir():
            continue
        try:
            directory.resolve(strict=True).relative_to(actions_root.resolve(strict=True))
            directory_metadata = directory.lstat()
        except (OSError, ValueError) as error:
            raise ValueError(f"W3 cleanup action log escaped containment: {error}") from error
        if not stat.S_ISDIR(directory_metadata.st_mode):
            raise ValueError("W3 cleanup action log must be a regular directory")
        for path in sorted(directory.glob("cleanup-action-*.json")):
            receipt = _read_contained_json(path, directory, "cleanup action receipt")
            _require_schema(receipt, "receipt_schema_version", 1)
            if receipt.get("closure_id") != closure_id:
                raise ValueError("W3 cleanup receipt closure binding does not match")
            receipts.append(
                {
                    "receipt_id": receipt.get("receipt_id"),
                    "closure_id": receipt.get("closure_id"),
                    "action": receipt.get("action"),
                    "actor_id": receipt.get("actor_id"),
                    "authorization_id": receipt.get("authorization_id"),
                    "evidence_refs": list(receipt.get("evidence_refs", [])),
                    "occurred_at": receipt.get("occurred_at"),
                    "verification": receipt.get("verification"),
                    "caller_attested_performed": receipt.get("performed") is True,
                    "deletion_inferred": False,
                    "receipt_path": str(path),
                }
            )
    return closures, receipts


def _collect_w3_projection(
    project_root: Path, workstreams: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Collect display evidence by invoking W3 Core policy and loaders only."""

    from project_orrery_core.review import (
        compute_integration_eligibility,
        inspect_review_package_freshness,
        load_review_package,
    )
    from project_orrery_core.workspace_cleanup import (
        CLEANUP_ACTIONS,
        WORKSPACE_CLASSIFICATIONS,
        compute_workspace_cleanup_eligibility,
        inventory_workspaces,
    )

    inventory = inventory_workspaces(project_root)
    _require_schema(inventory, "inventory_schema_version", 1)
    package_refs = {
        str(card["review_package_id"]): {
            "path": str(card.get("worktree_path")),
            "session_content_hash": card.get("review_package_content_hash"),
        }
        for card in workstreams
        if card.get("review_package_id")
    }
    closures_by_package = {
        str(entry["closure"]["review_package_id"]): dict(entry["closure"])
        for entry in inventory["entries"]
        if entry.get("closure", {}).get("review_package_id")
    }
    review_queue: list[dict[str, Any]] = []
    for package_id, reference in sorted(package_refs.items()):
        source_root = Path(reference["path"])
        package = load_review_package(source_root, package_id)
        _require_schema(package, "review_schema_version", 1)
        freshness = inspect_review_package_freshness(source_root, package_id)
        eligibility = compute_integration_eligibility(source_root, package_id)
        _require_schema(eligibility, "eligibility_schema_version", 1)
        policy = eligibility["review_policy"]
        closure = closures_by_package.get(package_id)
        review_queue.append(
            {
                "queue_status": "closed" if closure else "pending",
                "package_id": package_id,
                "package_content_hash": package["content_hash"],
                "session_content_hash": reference["session_content_hash"],
                "package_path": package.get("_git_private_path"),
                "workstream_id": package["workstream_id"],
                "generated_at": package["generated_at"],
                "freshness": "current" if freshness["fresh"] else "stale",
                "stale_reasons": list(freshness["stale_reasons"]),
                "risk": dict(package["risk"]),
                "human_approval": {
                    "count": policy["human_approval_count"],
                    "required": policy["required_human_reviewers"],
                    "capability": policy["required_approval_capability"],
                    "non_author_required": policy["non_author_reviewer_required"],
                    "non_author_count": policy["non_author_approval_count"],
                    "latest_decisions": list(policy["latest_decisions"]),
                },
                "integration": {
                    "eligible": eligibility["eligible"],
                    "reasons": list(eligibility["reasons"]),
                    "recommended_action": eligibility["recommended_action"],
                    "integration_ref_updated": eligibility["integration_ref_updated"],
                    "writes_performed": eligibility["writes_performed"],
                },
                "binding": dict(eligibility["binding"]),
                "evidence_refs": list(package["evidence"].get("evidence_refs", [])),
                "closure": closure,
            }
        )

    classification_counts = {key: 0 for key in WORKSPACE_CLASSIFICATIONS}
    inventory_entries: list[dict[str, Any]] = []
    cleanup: list[dict[str, Any]] = []
    for entry in inventory["entries"]:
        classification_counts[entry["classification"]] += 1
        closure = dict(entry["closure"])
        inventory_entries.append(
            {
                "workspace_id": entry["workspace_id"],
                "path": entry["path"],
                "resolved_path": entry["resolved_path"],
                "sources": list(entry["sources"]),
                "classification": entry["classification"],
                "classification_label": entry["classification_label"],
                "classification_source": entry["classification_source"],
                "protections": list(entry["protections"]),
                "unknown": list(entry["unknown"]),
                "estimated_reclaim_bytes": entry["estimated_reclaim_bytes"],
                "recommended_action": entry["recommended_action"],
                "closure": closure,
            }
        )
        if entry["recommended_action"] != "evaluate-cleanup-eligibility":
            continue
        package_id = closure.get("review_package_id")
        try:
            gate = compute_workspace_cleanup_eligibility(
                project_root,
                workspace_path=entry["path"],
                package=package_id,
            )
            _require_schema(gate, "cleanup_schema_version", 2)
        except _W3ProviderIncompatible:
            raise
        except ValueError as error:
            cleanup.append(
                {
                    "workspace_id": entry["workspace_id"],
                    "path": entry["path"],
                    "status": "unknown",
                    "eligible": None,
                    "reasons": [f"provider-unavailable:{type(error).__name__}"],
                    "unknown": [str(error)],
                    "estimated_reclaim_bytes": entry["estimated_reclaim_bytes"],
                    "closure_record": closure.get("record_path"),
                    "actions": {
                        action: {
                            "eligible": None,
                            "authorized": False,
                            "performed": False,
                            "implies_actions": [],
                            "reasons": ["cleanup-provider-unavailable"],
                        }
                        for action in CLEANUP_ACTIONS
                    },
                }
            )
        else:
            if set(gate["actions"]) != set(CLEANUP_ACTIONS):
                raise ValueError("W3 cleanup candidate did not provide four independent actions")
            if any(
                details.get("authorized") is not False
                or details.get("performed") is not False
                or details.get("implies_actions") != []
                for details in gate["actions"].values()
            ):
                raise ValueError("W3 read-only cleanup actions must remain independent and unperformed")
            cleanup.append(
                {
                    "workspace_id": gate["workspace"]["workspace_id"],
                    "path": gate["workspace"]["path"],
                    "status": "eligible" if gate["eligible"] else "blocked",
                    "eligible": gate["eligible"],
                    "reasons": list(gate["reasons"]),
                    "unknown": list(gate["unknown"]),
                    "estimated_reclaim_bytes": gate["estimated_reclaim_bytes"],
                    "closure_record": gate["closure_record"],
                    "actions": {key: dict(value) for key, value in gate["actions"].items()},
                }
            )

    closures, receipts = _load_closure_receipt_bundles(inventory_entries)
    return {
        "provider_schema_version": W3_PROJECTION_SCHEMA_VERSION,
        "status": "ready",
        "review_queue": review_queue,
        "inventory": {
            "inventory_schema_version": inventory["inventory_schema_version"],
            "inventory_id": inventory["inventory_id"],
            "content_hash": inventory["content_hash"],
            "classification_counts": classification_counts,
            "classification_labels": dict(WORKSPACE_CLASSIFICATIONS),
            "entries": inventory_entries,
            "source_contract": dict(inventory["source_contract"]),
        },
        "cleanup": cleanup,
        "closures": closures,
        "action_receipts": receipts,
        "writes_performed": False,
        "network_performed": False,
        "policy_owner": "project-orrery-core-w3",
    }


def _w3_summary(bundle: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    _require_schema(bundle, "provider_schema_version", W3_PROJECTION_SCHEMA_VERSION)
    packages = list(bundle.get("review_queue", []))
    pending = [item for item in packages if item.get("queue_status") == "pending"]
    stale = sum(item.get("freshness") != "current" for item in pending)
    eligible = sum(item.get("integration", {}).get("eligible") is True for item in pending)
    blockers = sum(len(item.get("integration", {}).get("reasons", [])) for item in pending)
    cleanup = list(bundle.get("cleanup", []))
    cleanup_eligible = sum(item.get("eligible") is True for item in cleanup)
    return {
        "review_queue": {
            "status": "empty" if not pending else "attention" if stale else "ready",
            "label": "No review packages" if not packages else f"{len(pending)} pending / {len(packages)} total",
            "detail": f"{stale} stale · human decisions remain authoritative",
            "source": "project-orrery-core-w3",
        },
        "integration_eligibility": {
            "status": "empty" if not pending else "ready" if eligible else "blocked",
            "label": "Unavailable · no review package" if not pending else f"{eligible} eligible",
            "detail": f"{blockers} Core-reported blockers · integration ref updated false",
            "source": "project-orrery-core-w3",
        },
        "cleanup_eligibility": {
            "status": "ready" if cleanup_eligible else "blocked" if cleanup else "empty",
            "label": f"{cleanup_eligible} eligible / {len(cleanup)} inventoried",
            "detail": "4 actions remain independent · authorized false · performed false",
            "source": "project-orrery-core-w3",
        },
    }


def _unavailable_worktree(record: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "workstream_id": "Unavailable",
        "worktree_id": "Unknown",
        "worktree_path": str(record.get("worktree", "Unknown")),
        "branch": _branch_label(record.get("branch")),
        "head": str(record.get("HEAD", "")),
        "integration_ref": "Unknown",
        "integration_oid": "Unknown",
        "merge_base": "Unknown",
        "ahead": None,
        "behind": None,
        "fact_scope": "unknown",
        "dirty": None,
        "dirty_entry_count": None,
        "untracked_count": None,
        "primary_subsystem_id": "Unknown",
        "affected_subsystem_ids": [],
        "scope_revision": None,
        "scope_path_count": None,
        "scope_paths": [],
        "lifecycle_phase": "unavailable",
        "runtime_condition": "stale-unknown",
        "evidence_freshness": "unknown",
        "session_state": "unavailable",
        "captured_at": None,
        "platform_session": None,
        "finding_counts": {},
        "findings": [],
        "availability": "unavailable",
        "unavailable_reason": reason,
        "has_session": False,
        "display_group": "unavailable",
        "is_primary": False,
    }


def _derive_health_projection(
    cards: Sequence[Mapping[str, Any]],
    findings: Sequence[Mapping[str, Any]],
    w3_evidence: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Route existing W1-W3 facts into delivery, reconciliation, and hygiene.

    This is a presentation-only classification.  It never changes a finding,
    workspace classification, review decision, or cleanup recommendation.
    """

    by_workstream = {
        str(card.get("workstream_id")): card
        for card in cards
        if card.get("workstream_id") not in {None, "Unavailable"}
    }
    current_delivery: list[Mapping[str, Any]] = []
    reconciliation_cards: list[Mapping[str, Any]] = []
    hygiene_cards: list[Mapping[str, Any]] = []
    primary_cards: list[Mapping[str, Any]] = []
    unregistered_candidates: list[Mapping[str, Any]] = []
    for card in cards:
        if card.get("is_primary"):
            primary_cards.append(card)
            continue
        has_session = card.get("has_session") is True
        phase = str(card.get("lifecycle_phase", "unavailable"))
        session_current = (
            has_session
            and card.get("availability") == "available"
            and card.get("session_state") != "stale"
            and card.get("evidence_freshness") == "current"
        )
        if session_current and phase in DELIVERY_PHASES:
            current_delivery.append(card)
        elif has_session and phase not in {"integrated", "closed"}:
            reconciliation_cards.append(card)
        elif not has_session and card.get("is_current"):
            unregistered_candidates.append(card)
        elif not has_session:
            hygiene_cards.append(card)

    delivery_ids = {str(card.get("workstream_id")) for card in current_delivery}
    reconciliation_ids = {
        str(card.get("workstream_id")) for card in reconciliation_cards
    }
    hygiene_ids = {str(card.get("workstream_id")) for card in hygiene_cards}
    hygiene_ids.update(str(card.get("workstream_id")) for card in primary_cards)

    current_blockers: list[dict[str, Any]] = []
    delivery_advisories: list[dict[str, Any]] = []
    reconciliation_findings: list[dict[str, Any]] = []
    hygiene_findings: list[dict[str, Any]] = []
    unknown_routes = Counter()
    for source in findings:
        finding = dict(source)
        ids = {str(value) for value in finding.get("workstream_ids", [])}
        missing = {value for value in ids if value not in by_workstream}
        kind = str(finding.get("kind", "unknown")).lower()
        all_current = len(ids) >= 2 and ids.issubset(delivery_ids)
        if kind == "direct" and all_current:
            current_blockers.append(finding)
            route = "delivery"
        elif kind != "unknown" and all_current:
            delivery_advisories.append(finding)
            route = "delivery"
        elif missing or ids.intersection(hygiene_ids) or kind == "unknown":
            hygiene_findings.append(finding)
            route = "hygiene"
        else:
            reconciliation_findings.append(finding)
            route = "reconciliation"
        if kind == "unknown":
            unknown_routes[route] += 1

    inventory = dict(w3_evidence.get("inventory", {})) if w3_evidence else {}
    inventory_counts = {
        str(key): int(value)
        for key, value in inventory.get("classification_counts", {}).items()
    }
    inventory_entries = list(inventory.get("entries", []))
    estimated_reclaim = sum(
        int(item.get("estimated_reclaim_bytes") or 0) for item in inventory_entries
    )
    stale_reviews: list[dict[str, Any]] = []
    current_reviews: list[dict[str, Any]] = []
    for item in (w3_evidence or {}).get("review_queue", []):
        if item.get("queue_status") != "pending":
            continue
        if (
            item.get("freshness") == "current"
            and str(item.get("workstream_id")) in delivery_ids
        ):
            current_reviews.append(dict(item))
        else:
            stale_reviews.append(dict(item))

    reconciliation_total = (
        len(reconciliation_cards)
        + len(reconciliation_findings)
        + len(stale_reviews)
        + len(unregistered_candidates)
    )
    hygiene_total = (
        inventory_counts.get("legacy-unmanaged", 0)
        + inventory_counts.get("unknown", 0)
    )
    return {
        "schema": "project-orrery-personal-health-v1",
        "authority": "derived-read-only",
        "delivery_now": {
            "workstream_count": len(current_delivery),
            "review_pending_count": len(current_reviews),
            "workstream_ids": sorted(delivery_ids),
            "current_blocker_count": len(current_blockers),
            "current_blockers": current_blockers,
            "advisories": delivery_advisories,
        },
        "reconciliation": {
            "total": reconciliation_total,
            "stale_session_count": len(reconciliation_cards),
            "stale_session_ids": sorted(reconciliation_ids),
            "finding_count": len(reconciliation_findings),
            "findings": reconciliation_findings,
            "stale_review_count": len(stale_reviews),
            "unregistered_candidate_count": len(unregistered_candidates),
            "unregistered_candidates": [
                str(card.get("branch", "Unknown")) for card in unregistered_candidates
            ],
        },
        "workspace_hygiene": {
            "total_worktrees": sum(inventory_counts.values()) or len(cards),
            "classification_counts": inventory_counts,
            "registered_active": inventory_counts.get("registered-active", 0),
            "review_pending": inventory_counts.get("review-integration-pending", 0),
            "legacy_unmanaged": inventory_counts.get("legacy-unmanaged", 0),
            "no_session": len(hygiene_cards) + len(unregistered_candidates),
            "retained": inventory_counts.get("evidence-retained", 0),
            "unknown": inventory_counts.get("unknown", 0),
            "debt_count": hygiene_total,
            "estimated_reclaim_bytes": estimated_reclaim,
            "finding_count": len(hygiene_findings),
            "findings": hygiene_findings,
            "primary_protected_count": len(primary_cards),
        },
        "unknown_accounting": {
            "total": sum(unknown_routes.values()),
            "delivery": unknown_routes["delivery"],
            "reconciliation": unknown_routes["reconciliation"],
            "hygiene": unknown_routes["hygiene"],
        },
    }


def build_personal_observatory_projection(
    project_root: Path,
    *,
    include_local_worktrees: bool = True,
    excluded_branches: Sequence[str] = (),
    w3_projection: Mapping[str, Any] | None = None,
    maintenance_projection: Mapping[str, Any] | None = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Aggregate W1/W2 contracts into a read-only Personal Mode snapshot.

    ``excluded_branches`` is a presentation-time isolation boundary.  Excluded
    worktrees are listed as Unavailable using the shared Git worktree registry,
    but their worktree files and private sessions are not opened.
    """

    from project_orrery_core.collaboration import (
        _normalized_path,
        _worktree_records,
        collect_scope_observation,
        collect_lineage_ancestry_proofs,
        compute_overlap_findings,
        inspect_worktree_status,
        reconcile_overlap_findings,
    )

    root = Path(project_root).expanduser().absolute()
    excluded = {
        value if value.startswith("refs/heads/") else f"refs/heads/{value}"
        for value in excluded_branches
    }
    records = _worktree_records(root) if include_local_worktrees else [
        {"worktree": str(root)}
    ]
    statuses: list[dict[str, Any]] = []
    scopes: list[dict[str, Any]] = []
    previous_findings: dict[str, dict[str, Any]] = {}
    unavailable_peers: list[dict[str, str]] = []
    unavailable_cards: list[dict[str, Any]] = []
    current_path = _normalized_path(root)

    for record in records:
        path = Path(str(record["worktree"]))
        branch = str(record.get("branch", ""))
        if branch in excluded:
            unavailable_cards.append(
                _unavailable_worktree(record, "excluded-worktree-contract-not-integrated")
            )
            unavailable_peers.append(
                {
                    "workstream_id": _branch_label(branch),
                    "reason": "excluded-worktree-contract-not-integrated",
                }
            )
            continue
        if not path.is_dir():
            unavailable_cards.append(_unavailable_worktree(record, "local-worktree-unavailable"))
            unavailable_peers.append(
                {
                    "workstream_id": _branch_label(branch),
                    "reason": "local-worktree-unavailable",
                }
            )
            continue
        try:
            status = inspect_worktree_status(path)
        except (OSError, ValueError) as error:
            unavailable_cards.append(
                _unavailable_worktree(record, f"status-unavailable:{type(error).__name__}")
            )
            unavailable_peers.append(
                {
                    "workstream_id": _branch_label(branch),
                    "reason": "local-worktree-status-unavailable",
                }
            )
            continue
        statuses.append(status)
        session = status["session"]["record"]
        if not isinstance(session, Mapping):
            unavailable_peers.append(
                {
                    "workstream_id": _branch_label(status["identity"]["branch"]),
                    "reason": "local-worktree-session-unavailable",
                }
            )
            continue
        for finding in session.get("findings", []):
            if isinstance(finding, Mapping) and finding.get("finding_id"):
                previous_findings[str(finding["finding_id"])] = dict(finding)
        try:
            scopes.append(collect_scope_observation(path, session=session))
        except (OSError, ValueError):
            unavailable_peers.append(
                {
                    "workstream_id": str(session.get("workstream_id", "unknown-workstream")),
                    "reason": "local-worktree-scope-unavailable",
                }
            )

    lineage_proofs = collect_lineage_ancestry_proofs(root, scopes)
    computed = compute_overlap_findings(
        scopes,
        unavailable_peers=unavailable_peers,
        lineage_ancestry_proofs=lineage_proofs,
    )
    reconciled = reconcile_overlap_findings(
        computed["findings"], list(previous_findings.values())
    )
    active_findings = reconciled["active"]
    scopes_by_worktree = {scope["worktree_id"]: scope for scope in scopes}
    findings_by_workstream: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in active_findings:
        for workstream_id in finding.get("workstream_ids", []):
            findings_by_workstream[str(workstream_id)].append(finding)

    cards: list[dict[str, Any]] = []
    for status in statuses:
        identity = status["identity"]
        session_info = status["session"]
        session = session_info["record"]
        scope = scopes_by_worktree.get(identity["worktree_id"])
        lifecycle = session_info.get("lifecycle") or {}
        workstream_id = (
            str(session.get("workstream_id"))
            if isinstance(session, Mapping)
            else _branch_label(identity["branch"])
        )
        relevant_findings = findings_by_workstream.get(workstream_id, [])
        finding_counts = Counter(str(item["kind"]) for item in relevant_findings)
        scope_paths = list(scope.get("path_entries", [])) if scope else []
        has_session = isinstance(session, Mapping)
        effective_phase = lifecycle.get("effective_phase", "unavailable")
        is_primary = bool(identity["is_primary"])
        session_current = (
            has_session
            and session_info["state"] != "stale"
            and lifecycle.get("evidence_freshness") == "current"
        )
        display_group = (
            "protected-primary"
            if is_primary
            else "active"
            if session_current and effective_phase in DELIVERY_PHASES
            else "reconciliation"
            if has_session and effective_phase not in {"integrated", "closed"}
            else "inactive"
            if has_session
            else "candidate-unregistered"
            if _normalized_path(Path(identity["worktree_path"])) == current_path
            else "worktree-only"
        )
        cards.append(
            {
                "workstream_id": workstream_id,
                "worktree_id": identity["worktree_id"],
                "worktree_path": identity["worktree_path"],
                "branch": _branch_label(identity["branch"]),
                "head": identity["head"],
                "integration_ref": identity["integration_ref"],
                "integration_oid": identity["integration_oid"],
                "merge_base": identity["merge_base"],
                "ahead": identity["ahead"],
                "behind": identity["behind"],
                "fact_scope": identity["fact_scope"],
                "dirty": identity["dirty"],
                "dirty_entry_count": identity["dirty_entry_count"],
                "untracked_count": identity["untracked_count"],
                "primary_subsystem_id": (
                    str(session.get("primary_subsystem_id", "Unknown"))
                    if isinstance(session, Mapping)
                    else "Unknown"
                ),
                "affected_subsystem_ids": (
                    list(session.get("affected_subsystem_ids", []))
                    if isinstance(session, Mapping)
                    else []
                ),
                "scope_revision": scope.get("scope_revision") if scope else None,
                "scope_path_count": len(scope_paths) if scope else None,
                "scope_paths": scope_paths,
                "lineage": (
                    dict(scope.get("lineage", {}))
                    if scope
                    else {
                        "lineage_schema_version": 1,
                        "status": "legacy-unknown",
                        "base_workstream_id": None,
                        "task_base_oid": None,
                        "validated_head": None,
                    }
                ),
                "lifecycle_phase": effective_phase,
                "declared_lifecycle_phase": lifecycle.get("declared_phase", "unavailable"),
                "runtime_condition": lifecycle.get("runtime_condition", "stale-unknown"),
                "evidence_freshness": lifecycle.get("evidence_freshness", "unknown"),
                "session_state": session_info["state"],
                "captured_at": (
                    str(session.get("captured_at")) if isinstance(session, Mapping) else None
                ),
                "platform_session": (
                    session.get("platform_session") if isinstance(session, Mapping) else None
                ),
                "review_package_id": (
                    session.get("review_package_id") if isinstance(session, Mapping) else None
                ),
                "review_package_content_hash": (
                    session.get("review_package_content_hash")
                    if isinstance(session, Mapping)
                    else None
                ),
                "finding_counts": dict(finding_counts),
                "findings": relevant_findings,
                "availability": "available",
                "unavailable_reason": None,
                "has_session": has_session,
                "display_group": display_group,
                "is_current": _normalized_path(Path(identity["worktree_path"])) == current_path,
                "is_primary": is_primary,
            }
        )
    cards.extend(unavailable_cards)
    parent_map = {
        str(item["workstream_id"]): str(item["base_workstream_id"])
        for item in computed.get("lineage_summaries", [])
        if item.get("status") == "current" and item.get("base_workstream_id")
    }
    for card in cards:
        workstream_id = str(card.get("workstream_id", ""))
        depth = 0
        root_id = workstream_id
        seen = {workstream_id}
        while root_id in parent_map and parent_map[root_id] not in seen:
            root_id = parent_map[root_id]
            seen.add(root_id)
            depth += 1
        card["lineage_depth"] = depth
        card["lineage_chain_root"] = root_id
    cards.sort(
        key=lambda item: (
            not item.get("is_current", False),
            item.get("availability") != "available",
            str(item.get("workstream_id", "")),
        )
    )

    subsystem_workstreams: dict[str, set[str]] = defaultdict(set)
    for card in cards:
        if card.get("display_group") != "active":
            continue
        subsystem_ids = [card["primary_subsystem_id"], *card["affected_subsystem_ids"]]
        for subsystem_id in subsystem_ids:
            if subsystem_id and subsystem_id != "Unknown":
                subsystem_workstreams[str(subsystem_id)].add(card["workstream_id"])
    subsystems = [
        {"subsystem_id": subsystem_id, "workstream_ids": sorted(workstream_ids)}
        for subsystem_id, workstream_ids in sorted(subsystem_workstreams.items())
    ]

    current = next((card for card in cards if card.get("is_current")), None)
    finding_counts = Counter(str(item["kind"]) for item in active_findings)
    attention: list[dict[str, str]] = []
    for kind in ("direct", "authority", "semantic", "unknown"):
        count = finding_counts.get(kind, 0)
        if count:
            attention.append(
                {
                    "kind": kind,
                    "severity": "critical" if kind == "direct" else "warning",
                    "label": f"{kind.title()} finding × {count}",
                }
            )
    freshness_counts: Counter[str] = Counter()
    for card in cards:
        if card["availability"] != "available":
            freshness_counts["unavailable"] += 1
        elif card.get("display_group") == "active" and card["session_state"] == "stale":
            freshness_counts[str(card["session_state"])] += 1
    for state in ("stale", "unavailable"):
        count = freshness_counts[state]
        if count:
            attention.append(
                {
                    "kind": "freshness",
                    "severity": "warning" if state != "unavailable" else "unknown",
                    "label": f"Evidence {state} × {count} local worktrees / Unknown",
                }
            )
    if not attention:
        attention.append(
            {
                "kind": "remote-unknown",
                "severity": "unknown",
                "label": "No local finding; remote and unreported work remain Unknown",
            }
        )

    w3_evidence: dict[str, Any] | None = None
    w3_error: dict[str, str] | None = None
    if w3_projection is None:
        excluded_isolation_boundary = bool(excluded) or any(
            card.get("unavailable_reason") == "excluded-worktree-contract-not-integrated"
            for card in cards
        )
        if excluded_isolation_boundary:
            w3_slots = _w3_slots(None)
            w3_error = {
                "type": "IsolationBoundary",
                "message": "excluded-worktree-isolation-boundary",
            }
        else:
            try:
                w3_evidence = _collect_w3_projection(root, cards)
                w3_slots = _w3_summary(w3_evidence)
            except Exception as error:
                w3_slots = _w3_slots(None)
                w3_error = {"type": type(error).__name__, "message": str(error)}
    elif "provider_schema_version" in w3_projection:
        try:
            _require_schema(
                w3_projection, "provider_schema_version", W3_PROJECTION_SCHEMA_VERSION
            )
            w3_evidence = dict(w3_projection)
            w3_slots = _w3_summary(w3_evidence)
        except Exception as error:
            w3_slots = _w3_slots(None)
            w3_error = {"type": type(error).__name__, "message": str(error)}
    else:
        w3_slots = _w3_slots(w3_projection)

    health = _derive_health_projection(cards, active_findings, w3_evidence)
    return {
        "projection_schema": PROJECTION_SCHEMA,
        "mode": "personal",
        "status": "ready",
        "read_only": True,
        "creates_project_facts": False,
        "writes_performed": False,
        "network_performed": False,
        "team_runtime_enabled": False,
        "captured_at": _now(captured_at),
        "project_root": str(root),
        "current": current,
        "workstreams": cards,
        "subsystems": subsystems,
        "findings": active_findings,
        "retired_findings": reconciled["retired"],
        "lineage_summaries": computed.get("lineage_summaries", []),
        "finding_counts": dict(finding_counts),
        "attention": attention,
        "health": health,
        "remote_observability": {
            "status": "unknown",
            "label": "Unknown",
            "detail": "Personal Mode has no Team runtime or remote telemetry",
        },
        "w3": w3_slots,
        "w3_evidence": w3_evidence,
        "w3_provider_error": w3_error,
        "maintenance": dict(maintenance_projection) if isinstance(maintenance_projection, Mapping) else {
            "status": "unavailable",
            "control_available": False,
            "queue": [],
            "authorizations": [],
            "receipts": [],
            "protected_reasons": {},
        },
        "source_contracts": [
            "worktree-status-v1",
            "scope-observation-v1",
            "overlap-report-v1",
            "collaboration-v1",
            *(
                ["review-package-v1", "workspace-inventory-v1", "workspace-cleanup-v2"]
                if w3_evidence
                else []
            ),
        ],
    }


def unavailable_personal_observatory_projection(error: Exception) -> dict[str, Any]:
    return {
        "projection_schema": PROJECTION_SCHEMA,
        "mode": "personal",
        "status": "unavailable",
        "read_only": True,
        "creates_project_facts": False,
        "writes_performed": False,
        "network_performed": False,
        "team_runtime_enabled": False,
        "captured_at": _now(),
        "error": {"type": type(error).__name__, "message": str(error)},
        "workstreams": [],
        "subsystems": [],
        "findings": [],
        "attention": [],
        "health": _derive_health_projection([], [], None),
        "remote_observability": {"status": "unknown", "label": "Unknown"},
        "w3": _w3_slots(None),
        "w3_evidence": None,
        "w3_provider_error": {"type": type(error).__name__, "message": str(error)},
        "maintenance": {
            "status": "unavailable",
            "control_available": False,
            "queue": [],
            "authorizations": [],
            "receipts": [],
            "protected_reasons": {},
        },
    }


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _value(value: object, suffix: str = "") -> str:
    return "待确认" if value is None else f"{value}{suffix}"


def _status_class(value: object) -> str:
    text = str(value or "unknown").lower().replace("_", "-")
    if text in {"active", "current", "canonical", "resolved", "ready"}:
        return "ok"
    if text in {"blocked-by-conflict", "failed", "direct", "l3"}:
        return "bad"
    if text in {"unknown", "unavailable", "stale-unknown", "absent"}:
        return "unknown"
    return "warn"


def _status_token(label: str, value: object) -> str:
    return (
        '<span class="po-token %s"><span>%s</span><b>%s</b></span>'
        % (_status_class(value), _esc(label), _esc(value))
    )


def _finding_rows(findings: Sequence[Mapping[str, Any]]) -> str:
    if not findings:
        return (
            '<div class="po-empty" data-state="no-local-finding">'
            "本机没有发现直接问题；远端证据不在当前观察范围内</div>"
        )
    rows = []
    for finding in findings:
        evidence = finding.get("path_evidence") or finding.get("validation_surfaces") or []
        detail = ", ".join(str(item) for item in evidence[:3]) or str(
            finding.get("resolution_reason") or "Evidence available in Scope detail"
        )
        rows.append(
            '<div class="po-finding %s"><span class="po-finding-kind">%s</span>'
            '<span class="po-finding-detail">%s</span>'
            '<span class="po-ack">%s · %s</span></div>'
            % (
                _status_class(finding.get("kind")),
                _esc(str(finding.get("kind", "unknown")).title()),
                _esc(detail),
                _esc(finding.get("disposition", "open")),
                _esc(finding.get("acknowledgement_progress", "0/0")),
            )
        )
    return "".join(rows)


def _human_phase(value: object) -> str:
    return {
        "created": "刚建立",
        "investigating": "调研中",
        "implementing": "实现中",
        "validating": "验证中",
        "review-ready": "等待审查",
        "integrated": "已集成",
        "closed": "已关闭",
        "unavailable": "阶段待确认",
        "unknown": "阶段待确认",
    }.get(str(value), str(value))


def _human_runtime(value: object) -> str:
    return {
        "active": "正在推进",
        "waiting-for-user": "等待确认",
        "paused": "已暂停",
        "blocked-by-conflict": "被冲突阻塞",
        "failed": "执行失败",
        "offline": "Agent 离线",
        "stale-unknown": "运行状态待确认",
        "unknown": "运行状态待确认",
    }.get(str(value), str(value))


def _human_freshness(value: object) -> str:
    return {
        "current": "证据最新",
        "stale": "证据已过期",
        "unknown": "证据待确认",
    }.get(str(value), str(value))


def _workstream_card(card: Mapping[str, Any]) -> str:
    branch = card.get("branch", "Unknown")
    title = str(card.get("workstream_id", branch))
    display_title = ("↳ " * int(card.get("lineage_depth", 0))) + title
    path_rows = "".join(
        '<li><code>%s</code><span>%s</span></li>'
        % (_esc(item.get("path", "Unknown")), _esc(" · ".join(item.get("sources", []))))
        for item in card.get("scope_paths", [])
    ) or '<li class="po-muted">当前没有可显示的范围路径</li>'
    agent = card.get("platform_session")
    agent_label = (
        f"{agent.get('adapter')} · {agent.get('session_id')}"
        if isinstance(agent, Mapping)
        else "Agent 会话暂不可用"
    )
    lineage = card.get("lineage") if isinstance(card.get("lineage"), Mapping) else {}
    if lineage.get("status") == "current":
        agent_label += " · 接续自 %s@%s" % (
            lineage.get("base_workstream_id", "Unknown"),
            _short_oid(lineage.get("task_base_oid")),
        )
    else:
        agent_label += " · 接续证据为历史状态或待确认"
    findings = card.get("findings", [])
    counts = card.get("finding_counts", {})
    finding_types = " · ".join(
        "%s %s" % (str(kind).title(), count)
        for kind, count in sorted(counts.items())
        if count
    ) or "本机无直接发现"
    affected = card.get("affected_subsystem_ids", [])
    return (
        '<details class="po-workstream" data-workstream="%s" data-session-state="%s">'
        '<summary class="po-work-summary"><div class="po-work-name"><span class="po-kicker">%s</span>'
        '<h4>%s</h4></div>'
        '<div class="po-work-now"><small>现在</small><b>%s</b><span>%s</span></div>'
        '<div class="po-work-scope"><small>影响范围</small><b>1 个主要模块</b><span>%s 个关联模块 · %s 条范围路径</span></div>'
        '<div class="po-work-signal"><small>信号</small><b>%s 项发现</b><span>%s · %s</span></div>'
        '<span class="po-open-label">查看证据</span></summary><div class="po-work-detail">'
        '<div class="po-tracks">%s%s%s</div>'
        '<div class="po-detail-grid"><div><b>集成目标</b><code>%s</code></div>'
        '<div><b>合并基点</b><code>%s</code></div><div><b>当前提交</b><code>%s</code></div>'
        '<div><b>领先／落后</b><span>+%s / −%s</span></div><div><b>任务登记</b><span>%s</span></div>'
        '<div><b>采集时间</b><span>%s</span></div><div class="po-detail-wide"><b>工作区</b><code>%s</code></div>'
        '</div><div class="po-evidence-note">%s · Scope r%s · %s changes · %s untracked · %s</div>'
        '<div class="po-detail-section"><b>发现与确认状态</b>%s</div>'
        '<div class="po-detail-section"><b>范围路径与来源</b><ul class="po-paths">%s</ul></div>'
        '</div></details>'
        % (
            _esc(title),
            _esc(card.get("session_state", "unknown")),
        "当前任务" if card.get("is_current") else "进行中的任务",
        _esc(display_title),
        _esc(_human_phase(card.get("lifecycle_phase", "unavailable"))),
        _esc(_human_runtime(card.get("runtime_condition", "stale-unknown"))),
        len(affected),
        _esc(_value(card.get("scope_path_count"))),
        len(findings),
        _esc(_human_freshness(card.get("evidence_freshness", "unknown"))),
        "有未提交改动" if card.get("dirty") else "工作区干净",
            _status_token("lifecycle", card.get("lifecycle_phase", "unavailable")),
            _status_token("runtime", card.get("runtime_condition", "stale-unknown")),
            _status_token("evidence", card.get("evidence_freshness", "unknown")),
            _esc(_short_oid(card.get("integration_oid"))),
            _esc(_short_oid(card.get("merge_base"))),
            _esc(_short_oid(card.get("head"))),
            _esc(_value(card.get("ahead"))),
            _esc(_value(card.get("behind"))),
            _esc(card.get("session_state", "unknown")),
            _esc(card.get("captured_at") or "Unknown"),
            _esc(card.get("worktree_path", "Unknown")),
            _esc(agent_label),
            _esc(_value(card.get("scope_revision"))),
            _esc(_value(card.get("dirty_entry_count"))),
            _esc(_value(card.get("untracked_count"))),
            _esc(finding_types),
            _finding_rows(findings),
            path_rows,
        )
    )


def _worktree_inventory_row(card: Mapping[str, Any]) -> str:
    group = str(card.get("display_group", "unavailable"))
    labels = {
        "inactive": "已集成或关闭的任务",
        "worktree-only": "没有任务登记",
        "candidate-unregistered": "候选尚未登记，无法判断交付状态",
        "reconciliation": "任务登记已过期，需要确认或关闭",
        "protected-primary": "受保护的主工作区，不属于普通任务",
        "unavailable": "证据暂不可用或待确认",
    }
    title = (
        card.get("workstream_id")
        if card.get("has_session")
        else card.get("branch", "Unknown")
    )
    note = card.get("unavailable_reason") or (
        "%s · %s finding(s)"
        % (card.get("fact_scope", "Unknown"), len(card.get("findings", [])))
    )
    return (
        '<div class="po-inventory-row" data-display-group="%s">'
        '<div><b>%s</b><span>%s</span></div><code>%s</code><span>%s</span><span>%s</span>'
        '</div>'
        % (
            _esc(group),
            _esc(title),
            _esc(labels.get(group, "本机已观察")),
            _esc(card.get("branch", "Unknown")),
            _esc(card.get("lifecycle_phase", "unavailable")),
            _esc(note),
        )
    )


def _size_label(value: object) -> str:
    if not isinstance(value, int):
        return "待确认"
    units = ("B", "KB", "MB", "GB")
    amount = float(value)
    unit = units[0]
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            break
        amount /= 1024
    return f"{amount:.1f} {unit}"


def _w3_evidence_html(bundle: Mapping[str, Any] | None) -> str:
    if not bundle:
        return '<div class="po-empty" data-state="w3-unavailable">W3 证据暂不可用；已保持安全降级</div>'
    reviews = "".join(
        '<details class="po-evidence-record"><summary><b>%s</b><span>%s · %s · approval %s/%s</span></summary>'
        '<div class="po-record-grid"><div><small>Risk</small><b>%s</b></div><div><small>Integration</small><b>%s</b></div>'
        '<div><small>Package hash</small><code>%s</code></div><div><small>Target OID</small><code>%s</code></div>'
        '<div><small>Candidate HEAD</small><code>%s</code></div><div><small>Scope hash</small><code>%s</code></div>'
        '<div class="po-record-wide"><small>Blockers / stale reasons</small><code>%s</code></div>'
        '<div class="po-record-wide"><small>Git-private package</small><code>%s</code></div></div></details>'
        % (
            _esc(item.get("workstream_id", "Unknown")),
            _esc(item.get("queue_status", "unknown")),
            _esc(item.get("freshness", "unknown")),
            _esc(item.get("human_approval", {}).get("count", 0)),
            _esc(item.get("human_approval", {}).get("required", "Unknown")),
            _esc(item.get("risk", {}).get("level", item.get("risk", {}).get("risk_level", "Unknown"))),
            _esc("eligible" if item.get("integration", {}).get("eligible") else "blocked"),
            _esc(item.get("package_content_hash", "Unknown")),
            _esc(item.get("binding", {}).get("target_oid", "Unknown")),
            _esc(item.get("binding", {}).get("candidate_head", "Unknown")),
            _esc(item.get("binding", {}).get("scope_fingerprint", "Unknown")),
            _esc(" · ".join([*item.get("integration", {}).get("reasons", []), *item.get("stale_reasons", [])]) or "None reported"),
            _esc(item.get("package_path", "Unknown")),
        )
        for item in bundle.get("review_queue", [])
    ) or '<div class="po-empty" data-state="no-review-package">No review packages in bound Workstream sessions</div>'
    inventory = bundle.get("inventory", {})
    classes = "".join(
        '<div><span>%s</span><b>%s</b></div>'
        % (_esc(inventory.get("classification_labels", {}).get(key, key)), _esc(count))
        for key, count in inventory.get("classification_counts", {}).items()
    )
    entries = "".join(
        '<div class="po-w3-inventory-row"><div><b>%s</b><code>%s</code></div><span>%s</span><span>%s</span><span>%s</span></div>'
        % (
            _esc(item.get("classification_label", "Unknown")),
            _esc(item.get("path", "Unknown")),
            _esc("protected: " + (", ".join(item.get("protections", [])) or "none")),
            _esc("Unknown: " + (", ".join(item.get("unknown", [])) or "none")),
            _esc(_size_label(item.get("estimated_reclaim_bytes"))),
        )
        for item in inventory.get("entries", [])
    ) or '<div class="po-empty">没有边界内工作区记录</div>'
    cleanup = "".join(
        '<details class="po-evidence-record"><summary><b>%s</b><span>%s · %s</span></summary>'
        '<div class="po-actions">%s</div><p class="po-record-note">%s</p></details>'
        % (
            _esc(item.get("path", "Unknown")),
            _esc(item.get("status", "unknown")),
            _esc(_size_label(item.get("estimated_reclaim_bytes"))),
            "".join(
                '<div><b>%s</b><span>eligible %s · authorized %s · performed %s</span><small>implies %s</small></div>'
                % (
                    _esc(action),
                    _esc(details.get("eligible", "Unknown")),
                    _esc(details.get("authorized", False)),
                    _esc(details.get("performed", False)),
                    _esc(details.get("implies_actions", [])),
                )
                for action, details in item.get("actions", {}).items()
            ),
            _esc(" · ".join([*item.get("reasons", []), *item.get("unknown", [])]) or "No Core blocker reported"),
        )
        for item in bundle.get("cleanup", [])
    ) or '<div class="po-empty">Cleanup eligibility Unavailable / Unknown</div>'
    closures = "".join(
        '<div class="po-receipt"><b>%s · %s</b><span>closure evidence only</span>'
        '<code>%s</code><small>%s · %s</small></div>'
        % (
            _esc(item.get("closure_id", "Unknown")),
            _esc(item.get("closure_reason", "Unknown")),
            _esc(item.get("final_oid", "Unknown")),
            _esc(item.get("review_package_id", "Unknown")),
            _esc(item.get("record_path", "Unknown")),
        )
        for item in bundle.get("closures", [])
    ) or '<div class="po-empty">No Git-private closure records in bounded inventory</div>'
    receipts = "".join(
        '<div class="po-receipt"><b>%s · %s</b><span>caller-attested=%s · deletion inferred=false</span>'
        '<code>%s</code><small>%s</small></div>'
        % (
            _esc(item.get("action", "Unknown")),
            _esc(item.get("receipt_id", "Unknown")),
            _esc(item.get("caller_attested_performed", False)),
            _esc(item.get("authorization_id", "Unknown")),
            _esc(item.get("receipt_path", "Unknown")),
        )
        for item in bundle.get("action_receipts", [])
    ) or '<div class="po-empty">No caller-attested cleanup action receipts</div>'
    return (
        '<section><h4>Review packages · evidence first</h4>%s</section>'
        '<section><h4>Bounded workspace inventory · all seven classes</h4>'
        '<div class="po-class-counts">%s</div><code class="po-hashline">%s · %s</code><div class="po-w3-inventory">%s</div></section>'
        '<section><h4>Cleanup eligibility · independent actions</h4>%s</section>'
        '<section><h4>Closure / action receipts</h4><p class="po-record-note">Closure records establish traceability. Action receipts are caller-attested evidence; neither proves a path or branch was deleted.</p>%s%s</section>'
        % (
            reviews,
            classes,
            _esc(inventory.get("inventory_id", "Unknown")),
            _esc(inventory.get("content_hash", "Unknown")),
            entries,
            cleanup,
            closures,
            receipts,
        )
    )


PERSONAL_OBSERVATORY_CSS = r"""
.po-shell{--po-cyan:#63d6cf;--po-amber:#f2ba5e;--po-red:#ff786b;--po-dim:#758097;
 margin:0 0 24px;border:1px solid var(--line);border-radius:16px;overflow:hidden;
 background:linear-gradient(180deg,rgba(127,176,255,.055),transparent 220px),var(--bg)}
.po-mast{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;padding:22px 24px 18px;
 border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(99,214,207,.07),transparent 58%)}
.po-kicker{display:block;color:var(--po-cyan);font:700 10px/1.3 "Cascadia Code",Consolas,monospace;
 letter-spacing:.14em;text-transform:uppercase}.po-mast h2{margin:4px 0 4px;font-size:26px;letter-spacing:-.025em}
.po-mast p,.po-ws-head p{margin:0;color:var(--mut);font-size:12.5px}.po-lock{align-self:start;display:flex;
 gap:7px;align-items:center;color:var(--mut);font:600 11px/1.2 "Cascadia Code",Consolas,monospace;
 border:1px solid var(--line);padding:7px 10px;border-radius:7px}.po-lock::before{content:"●";color:var(--po-cyan)}
.po-zone{padding:20px 24px;border-bottom:1px solid var(--line)}.po-zone:last-child{border-bottom:0}
.po-zone-head{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:13px}
.po-zone-head h3{margin:0;font-size:15px;letter-spacing:.01em}.po-zone-head span{color:var(--mut);font-size:11.5px}
.po-project-grid{display:grid;grid-template-columns:1.2fr repeat(3,minmax(120px,.7fr));gap:1px;background:var(--line);
 border:1px solid var(--line);border-radius:11px;overflow:hidden}.po-project-cell{min-width:0;padding:13px 14px;background:var(--bg2)}
.po-project-cell small{display:block;color:var(--mut);font:700 9.5px/1.2 "Cascadia Code",Consolas,monospace;
 letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}.po-project-cell b{display:block;font-size:14px;overflow-wrap:anywhere}
.po-project-cell code{display:inline-block;margin-top:3px}.po-attention-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:12px}
.po-attention,.po-w3{border:1px solid var(--line);border-radius:11px;background:var(--bg2);padding:13px}
.po-alert{display:flex;gap:10px;align-items:center;padding:8px 2px;border-bottom:1px solid var(--line);font-size:12.5px}
.po-alert:last-child{border-bottom:0}.po-alert::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--po-amber)}
.po-alert.unknown::before{background:var(--po-dim)}.po-alert.critical::before{background:var(--po-red)}
.po-w3-row{display:grid;grid-template-columns:1fr auto;gap:9px;padding:8px 2px;border-bottom:1px solid var(--line);font-size:12px}
.po-w3-row:last-child{border-bottom:0}.po-w3-row small{grid-column:1/-1;color:var(--mut)}
.po-workstreams{display:grid;grid-template-columns:minmax(0,1fr);gap:10px}.po-workstream{min-width:0;
 border:1px solid var(--line);border-radius:12px;background:var(--bg2);padding:15px;box-shadow:inset 3px 0 0 var(--po-cyan)}
.po-workstream.unavailable{box-shadow:inset 3px 0 0 var(--po-dim)}.po-ws-head{display:flex;gap:10px;align-items:start;
 justify-content:space-between}.po-ws-head h4{margin:3px 0 1px;font-size:15px;overflow-wrap:anywhere}.po-scope{border:1px solid var(--line);
 padding:3px 8px;border-radius:5px;font:700 10px/1.4 "Cascadia Code",Consolas,monospace;text-transform:uppercase}
.po-scope.ok{color:var(--po-cyan)}.po-scope.warn{color:var(--po-amber)}.po-scope.unknown{color:var(--po-dim)}
.po-tracks{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}.po-token{display:inline-grid;grid-template-columns:auto auto;
 gap:5px;align-items:center;border:1px solid var(--line);padding:4px 7px;border-radius:6px;font:10px/1.2 "Cascadia Code",Consolas,monospace}
.po-token span{color:var(--mut)}.po-token.ok b{color:var(--po-cyan)}.po-token.warn b{color:var(--po-amber)}
.po-token.bad b{color:var(--po-red)}.po-token.unknown b{color:var(--po-dim)}.po-summary-grid{display:grid;
 grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--line);border-radius:8px;overflow:hidden}
.po-summary-grid>div{display:flex;flex-direction:column;gap:2px;min-width:0;padding:9px 11px;border-right:1px solid var(--line)}
.po-summary-grid>div:last-child{border-right:0}.po-summary-grid small{color:var(--mut);font:700 9px/1.2 "Cascadia Code",Consolas,monospace;letter-spacing:.08em}
.po-summary-grid b{font-size:12px;overflow-wrap:anywhere}.po-summary-grid span{color:var(--mut);font-size:10.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-finding{display:grid;grid-template-columns:72px minmax(0,1fr) auto;gap:8px;
 padding:7px 0;border-top:1px solid var(--line);font-size:11px}.po-finding-kind{font-weight:800;text-transform:uppercase}
.po-finding.bad .po-finding-kind{color:var(--po-red)}.po-finding.warn .po-finding-kind{color:var(--po-amber)}
.po-finding.unknown .po-finding-kind{color:var(--po-dim)}.po-finding-detail{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-ack{color:var(--mut);white-space:nowrap}.po-empty{padding:8px 0;color:var(--mut);font-size:11.5px;border-top:1px solid var(--line)}
.po-workstream details{margin-top:8px;border-top:1px solid var(--line);padding-top:8px}.po-workstream summary{cursor:pointer;
 color:var(--acc);font-size:11.5px}.po-detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.po-detail-grid>div{display:flex;flex-direction:column;gap:3px;min-width:0}.po-detail-grid b{font-size:10px;color:var(--mut)}
.po-detail-wide{grid-column:1/-1}.po-detail-section{margin-top:12px}.po-detail-section>b{display:block;color:var(--mut);font-size:10px;margin-bottom:5px}
.po-paths{list-style:none;margin:10px 0 0;padding:0;max-height:180px;overflow:auto}.po-paths li{display:flex;justify-content:space-between;
 gap:12px;padding:5px 0;border-top:1px solid var(--line);font-size:10.5px}.po-paths span{color:var(--mut)}
.po-subsystems{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.po-subsystem{border-left:2px solid var(--po-cyan);
 background:var(--bg2);padding:10px 11px;min-width:0}.po-subsystem b{display:block;font-size:12px;margin-bottom:3px;overflow-wrap:anywhere}
.po-subsystem span{display:block;color:var(--mut);font-size:10.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-inventory{margin-top:12px;border:1px solid var(--line);border-radius:10px;background:var(--bg2);overflow:hidden}
.po-inventory>summary{cursor:pointer;padding:11px 13px;color:var(--acc);font-size:12px}.po-inventory-body{border-top:1px solid var(--line)}
.po-inventory-row{display:grid;grid-template-columns:minmax(180px,1.2fr) minmax(140px,1fr) 100px minmax(180px,1fr);gap:12px;
 align-items:center;padding:9px 13px;border-top:1px solid var(--line);font-size:10.5px}.po-inventory-row:first-child{border-top:0}
.po-inventory-row>div{display:flex;flex-direction:column;min-width:0}.po-inventory-row b,.po-inventory-row span,.po-inventory-row code{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.po-inventory-row>span,.po-inventory-row>div span{color:var(--mut)}
.po-muted{color:var(--mut)!important}.po-foot{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;
 color:var(--mut);font:10px/1.5 "Cascadia Code",Consolas,monospace;padding:11px 24px;background:var(--bg2)}
.po-brief{padding:28px 28px 24px;border-bottom:1px solid var(--line);background:var(--bg2)}
.po-brief-top{display:flex;justify-content:space-between;align-items:start;gap:24px}.po-brief h2{font-size:30px;line-height:1.18;
 letter-spacing:-.035em;margin:7px 0 8px;color:var(--strong)}.po-brief-top p{max-width:720px;margin:0;color:var(--fg);font-size:15px;line-height:1.7}
.po-brief-grid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(260px,.65fr);gap:24px;margin-top:24px}
.po-signals{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.po-signals>div{padding:13px 14px 12px;border-right:1px solid var(--line)}.po-signals>div:last-child{border-right:0}
.po-signals b{display:block;font-size:24px;line-height:1.1;margin-bottom:5px;color:var(--strong)}.po-signals span{color:var(--mut);font-size:11px}
.po-signals .critical b{color:var(--po-red)}.po-proof{display:grid;gap:7px;border-left:1px solid var(--line);padding-left:18px}
.po-proof>div{display:flex;justify-content:space-between;gap:14px;align-items:baseline}.po-proof small{color:var(--mut);font-size:10px}
.po-proof b,.po-proof code{font-size:10.5px;text-align:right}.po-priorities{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.po-priorities li{display:grid;grid-template-columns:10px minmax(0,1fr);gap:13px;padding:13px 2px;border-bottom:1px solid var(--line)}
.po-priority-mark{width:8px;height:8px;margin-top:7px;border-radius:50%;background:var(--po-amber)}
.po-priorities li.critical .po-priority-mark{background:var(--po-red)}.po-priorities li.unknown .po-priority-mark{background:var(--po-dim)}
.po-priorities b{font-size:13.5px}.po-priorities p{margin:2px 0 0;color:var(--mut);font-size:11.5px;line-height:1.55}
.po-workstream{padding:0;box-shadow:none;border-radius:9px;background:var(--bg2)}.po-workstream[open]{border-color:color-mix(in srgb,var(--acc) 45%,var(--line))}
.po-workstream>.po-work-summary{display:grid;grid-template-columns:minmax(210px,1.35fr) minmax(130px,.75fr) minmax(150px,.9fr) minmax(140px,.8fr) auto;
 gap:14px;align-items:center;padding:13px 14px;cursor:pointer;list-style:none;color:var(--fg)}.po-work-summary::-webkit-details-marker{display:none}
.po-work-summary:hover{background:var(--bg3)}.po-work-name,.po-work-now,.po-work-scope,.po-work-signal{display:flex;flex-direction:column;min-width:0}
.po-work-name h4{font-size:13px;margin:2px 0 3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.po-work-name code{width:max-content;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-work-summary small{font-size:9px;color:var(--mut);letter-spacing:.06em;text-transform:uppercase}.po-work-summary b{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.po-work-summary div>span:not(.po-kicker){font-size:10.5px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.po-open-label{color:var(--acc);font-size:10px;white-space:nowrap}.po-workstream[open] .po-open-label{font-size:0}.po-workstream[open] .po-open-label::after{content:"收起";font-size:10px}
.po-work-detail{padding:0 14px 14px;border-top:1px solid var(--line)}.po-evidence-note{margin:10px 0;color:var(--mut);font-size:10.5px}
.po-subsystems{grid-template-columns:repeat(2,minmax(0,1fr))}.po-subsystem{display:flex;justify-content:space-between;gap:16px;align-items:center;
 border-left:0;border-bottom:1px solid var(--line);padding:10px 2px;background:transparent}.po-subsystem div{min-width:0}.po-subsystem code{max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.po-vault{margin:0;border-top:1px solid var(--line);background:var(--bg2)}.po-vault>summary{display:flex;justify-content:space-between;gap:20px;
 align-items:center;padding:15px 24px;cursor:pointer;list-style:none}.po-vault>summary::-webkit-details-marker{display:none}.po-vault>summary div{display:flex;flex-direction:column}
.po-vault>summary b{font-size:13px}.po-vault>summary span{color:var(--mut);font-size:10.5px}.po-vault-body{padding:0 24px 20px;border-top:1px solid var(--line)}
.po-vault-body h4{font-size:11px;margin:16px 0 7px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}
.po-evidence-record{border-top:1px solid var(--line);padding:9px 0}.po-evidence-record>summary{display:flex;justify-content:space-between;
 gap:12px;cursor:pointer;font-size:11px}.po-evidence-record>summary span,.po-record-note{color:var(--mut);font-size:10.5px}
.po-record-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:10px}.po-record-grid>div{display:flex;flex-direction:column;min-width:0}
.po-record-grid small{color:var(--mut);font-size:9px}.po-record-grid code{overflow:hidden;text-overflow:ellipsis}.po-record-wide{grid-column:1/-1}
.po-class-counts{display:grid;grid-template-columns:repeat(7,minmax(90px,1fr));gap:1px;background:var(--line);border:1px solid var(--line)}
.po-class-counts>div{display:flex;flex-direction:column;padding:8px;background:var(--bg)}.po-class-counts span{color:var(--mut);font-size:9px}.po-class-counts b{font-size:15px}
.po-hashline{display:block;margin:9px 0;overflow:hidden;text-overflow:ellipsis}.po-w3-inventory{border-top:1px solid var(--line)}
.po-w3-inventory-row{display:grid;grid-template-columns:minmax(220px,1.35fr) 1fr 1fr 80px;gap:10px;padding:9px 0;border-bottom:1px solid var(--line);font-size:10px}
.po-w3-inventory-row>div{display:flex;flex-direction:column;min-width:0}.po-w3-inventory-row code{overflow:hidden;text-overflow:ellipsis}.po-w3-inventory-row>span{color:var(--mut)}
.po-actions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;margin-top:9px;background:var(--line);border:1px solid var(--line)}
.po-actions>div{display:flex;flex-direction:column;gap:3px;padding:8px;background:var(--bg)}.po-actions b{font-size:10px}.po-actions span,.po-actions small{color:var(--mut);font-size:9px}
.po-receipt{display:grid;grid-template-columns:minmax(160px,1fr) minmax(180px,1fr);gap:5px 12px;padding:8px 0;border-top:1px solid var(--line);font-size:10px}
.po-receipt code,.po-receipt small{overflow:hidden;text-overflow:ellipsis}.po-receipt span,.po-receipt small{color:var(--mut)}
@media(max-width:900px){.po-project-grid{grid-template-columns:1fr 1fr}
 .po-attention-grid{grid-template-columns:1fr}.po-subsystems{grid-template-columns:1fr 1fr}.po-brief-grid{grid-template-columns:1fr}
 .po-proof{border-left:0;border-top:1px solid var(--line);padding:12px 0 0}.po-workstream>.po-work-summary{grid-template-columns:minmax(190px,1.2fr) repeat(3,minmax(110px,.8fr))}.po-open-label{display:none}}
@media(max-width:640px){.po-shell{border-left:0;border-right:0;border-radius:0;
 margin:0 -18px 24px}
 header.top{gap:8px;padding:0 12px}header.top h1{min-width:0;overflow:hidden;text-overflow:ellipsis}
 header.top .sub,header.top .searchwrap{display:none}.rightgrp{gap:6px}
 .po-mast{grid-template-columns:1fr;padding:18px}.po-lock{justify-self:start}.po-zone{padding:17px 18px}
 .po-project-grid{grid-template-columns:1fr}.po-workstream{padding:0}.po-tracks{display:grid;grid-template-columns:1fr}
 .po-token{justify-content:space-between}.po-summary-grid{grid-template-columns:1fr}.po-summary-grid>div{border-right:0;border-top:1px solid var(--line)}
 .po-summary-grid>div:first-child{border-top:0}.po-finding{grid-template-columns:1fr auto}
 .po-finding-detail{grid-column:1/-1;white-space:normal}.po-detail-grid{grid-template-columns:1fr}.po-subsystems{grid-template-columns:1fr}
 .po-inventory-row{grid-template-columns:1fr}.po-inventory-row>span{white-space:normal}.po-inventory-row>code{width:max-content;max-width:100%}
 .po-foot{padding:11px 18px}.po-zone-head{align-items:start;flex-direction:column;gap:3px}
 .po-brief{padding:22px 18px}.po-brief-top{display:block}.po-brief h2{font-size:27px}.po-lock{margin-top:16px;width:max-content;max-width:100%}
 .po-signals{grid-template-columns:1fr 1fr}.po-signals>div:nth-child(2){border-right:0}.po-signals>div:nth-child(-n+2){border-bottom:1px solid var(--line)}
 .po-signals b{font-size:21px}.po-proof>div{align-items:start}.po-workstream>.po-work-summary{grid-template-columns:1fr 1fr;padding:13px}
 .po-work-name{grid-column:1/-1;border-bottom:1px solid var(--line);padding-bottom:10px}.po-work-signal{grid-column:1/-1}
 .po-work-detail{padding:0 13px 13px}.po-subsystems{grid-template-columns:1fr}.po-subsystem{align-items:start;flex-direction:column;gap:5px}.po-subsystem code{max-width:100%}
 .po-vault>summary{padding:14px 18px}.po-vault-body{padding:0 18px 18px}.po-record-grid{grid-template-columns:1fr}
 .po-record-wide{grid-column:auto}.po-class-counts{grid-template-columns:1fr 1fr}.po-w3-inventory-row,.po-actions,.po-receipt{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){.po-shell *{scroll-behavior:auto!important;transition:none!important}}
"""


MAINTENANCE_OBSERVATORY_CSS = r"""
.mo-shell{--mo-green:#63d6cf;--mo-amber:#f2ba5e;--mo-red:#ff786b;margin:0 0 24px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--bg);min-width:0}
.mo-head{display:grid;grid-template-columns:minmax(0,1fr) minmax(300px,auto);gap:22px;align-items:start;padding:18px 22px;background:linear-gradient(90deg,rgba(99,214,207,.08),transparent 68%);border-bottom:1px solid var(--line)}
.mo-kicker{color:var(--mo-green);font:700 9px/1.3 "Cascadia Code",Consolas,monospace;letter-spacing:.13em}.mo-head h2{margin:4px 0;font-size:25px;letter-spacing:-.025em}.mo-head p{margin:0;color:var(--mut);font-size:11.5px;max-width:720px}
.mo-head-actions{display:grid;justify-items:end;gap:9px;min-width:0}.mo-boundary{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:5px;color:var(--mut);font-size:9.5px}.mo-boundary span{border:1px solid var(--line);border-radius:999px;padding:4px 7px;white-space:nowrap}.mo-boundary .current{color:var(--mo-green)}
.mo-refresh-control{display:flex;align-items:center;justify-content:flex-end;gap:9px;min-width:0}.mo-refresh-state{display:block;width:128px;min-height:13px;color:var(--mut);font-size:9.5px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mo-refresh-state.error{color:var(--mo-red)}
.mo-button{appearance:none;border:1px solid var(--line);border-radius:7px;background:var(--bg3);color:var(--fg);padding:8px 11px;font:700 10px/1.2 inherit;cursor:pointer;white-space:nowrap}.mo-button:hover:not(:disabled){border-color:var(--mo-green);color:var(--mo-green)}.mo-button:focus-visible,.mo-filter:focus-visible,.mo-pager button:focus-visible,.mo-row details>summary:focus-visible{outline:2px solid var(--mo-green);outline-offset:2px}.mo-button:disabled{opacity:.45;cursor:not-allowed}.mo-button.danger{color:var(--mo-red)}
.mo-progress{height:2px;background:var(--line);overflow:hidden}.mo-progress.running::after{content:"";display:block;width:32%;height:100%;background:var(--mo-green);animation:mo-scan 1.1s ease-in-out infinite alternate}@keyframes mo-scan{from{transform:translateX(-35%)}to{transform:translateX(280%)}}
.mo-signals{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border-bottom:1px solid var(--line)}.mo-signals>div{padding:11px 16px;background:var(--bg2)}.mo-signals small{display:block;color:var(--mut);font-size:9px}.mo-signals b{display:block;margin-top:3px;font-size:17px}.mo-signals .safe b{color:var(--mo-green)}.mo-signals .attention b{color:var(--mo-amber)}
.mo-warning{margin:10px 20px 0;padding:7px 10px;border:1px dashed color-mix(in srgb,var(--mo-amber) 70%,var(--line));border-radius:7px;color:var(--mut);font-size:9.5px}.mo-warning summary{cursor:pointer;color:var(--mo-amber);font-weight:700}.mo-warning p{margin:5px 0 0}.mo-warning code{display:block;margin-top:5px;white-space:normal;overflow-wrap:anywhere}
.mo-main{padding:16px 20px 18px;min-width:0}.mo-queue-head{display:flex;align-items:end;justify-content:space-between;gap:16px;margin-bottom:9px}.mo-queue-head h3{margin:0;font-size:13px}.mo-queue-head p{margin:3px 0 0;color:var(--mut);font-size:10px}.mo-safe-note{color:var(--mut);font-size:10px;text-align:right}.mo-safe-note b{color:var(--mo-green)}
.mo-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:9px}.mo-filters{display:flex;flex-wrap:wrap;gap:5px}.mo-filter{border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--mut);padding:6px 9px;font:700 9.5px/1 inherit;cursor:pointer}.mo-filter:hover,.mo-filter[aria-pressed="true"]{border-color:var(--mo-green);color:var(--fg);background:rgba(99,214,207,.08)}
.mo-pager{display:flex;align-items:center;gap:7px;color:var(--mut);font-size:9.5px;white-space:nowrap}.mo-pager button{width:28px;height:28px;border:1px solid var(--line);border-radius:6px;background:var(--bg3);color:var(--fg);cursor:pointer}.mo-pager button:disabled{opacity:.35;cursor:not-allowed}
.mo-table{border:1px solid var(--line);border-radius:9px;overflow:hidden;min-width:0}.mo-table-head,.mo-row-grid{display:grid;grid-template-columns:minmax(170px,1.15fr) minmax(95px,.62fr) minmax(220px,1.35fr) minmax(118px,.75fr) minmax(92px,auto);gap:12px;align-items:center}.mo-table-head{padding:7px 11px;background:var(--bg3);color:var(--mut);font-size:8.5px;text-transform:uppercase;letter-spacing:.07em}.mo-row{border-top:1px solid var(--line);background:var(--bg2);min-width:0}.mo-row:first-of-type{border-top:0}.mo-row-grid{padding:9px 11px;min-height:58px}.mo-cell{min-width:0}.mo-cell b,.mo-cell span,.mo-cell time{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.mo-cell b{font-size:11px}.mo-cell span,.mo-cell time{color:var(--mut);font-size:9.5px}.mo-cell .mo-sub{margin-top:3px}.mo-row-state{width:max-content;max-width:100%;border-radius:999px;padding:4px 7px;border:1px solid var(--line);font:700 9px/1 "Cascadia Code",Consolas,monospace}.mo-row[data-maintenance-view-state="eligible"] .mo-row-state{color:var(--mo-green);border-color:color-mix(in srgb,var(--mo-green) 45%,var(--line))}.mo-row[data-maintenance-view-state="attention"] .mo-row-state{color:var(--mo-amber);border-color:color-mix(in srgb,var(--mo-amber) 45%,var(--line))}.mo-row-action{justify-self:end}.mo-row-action .mo-button{padding:7px 9px}.mo-row details{grid-column:1/-1;min-width:0}.mo-row details>summary{width:max-content;cursor:pointer;color:var(--mut);font-size:9.5px}.mo-row-detail{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px;margin-top:8px;padding:9px 10px;background:var(--bg);border-radius:7px}.mo-row-detail div{min-width:0}.mo-row-detail dt{color:var(--mut);font-size:8.5px}.mo-row-detail dd{margin:2px 0 0;font:9.5px/1.45 "Cascadia Code",Consolas,monospace;overflow-wrap:anywhere}.mo-row-detail .wide{grid-column:1/-1}
.mo-empty{padding:16px;color:var(--mut);font-size:10.5px}.mo-table-empty{border:1px dashed var(--line);border-radius:8px;text-align:center}.mo-reason{display:flex;justify-content:space-between;gap:10px;border-top:1px solid var(--line);padding:7px 0;font-size:9.5px}.mo-policy{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 14px;font-size:9.5px}.mo-policy span{color:var(--mut)}
.mo-technical{margin:0 20px 18px;border-top:1px solid var(--line);padding-top:10px}.mo-technical>summary{cursor:pointer;color:var(--mut);font-size:10.5px;font-weight:700}.mo-technical-body{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:12px}.mo-technical h4{margin:0 0 7px;font-size:10px}.mo-history>summary{cursor:pointer;font-size:9.5px}.mo-boundaries{display:grid;gap:7px}.mo-boundaries div{padding-left:8px;border-left:2px solid var(--line)}.mo-boundaries b{display:block;font-size:9.5px}.mo-boundaries span{display:block;margin-top:2px;color:var(--mut);font-size:9px}
@media(max-width:980px){.mo-table-head,.mo-row-grid{grid-template-columns:minmax(150px,1.05fr) 90px minmax(170px,1.2fr) 105px auto}.mo-technical-body{grid-template-columns:1fr 1fr}}
@media(max-width:720px){.mo-head{grid-template-columns:1fr}.mo-head-actions{justify-items:start}.mo-boundary,.mo-refresh-control{justify-content:flex-start}.mo-signals{grid-template-columns:1fr 1fr}.mo-table-head{display:none}.mo-row-grid{grid-template-columns:minmax(0,1fr) auto;gap:6px 10px;padding:9px 11px}.mo-cell.workspace{grid-column:1/2;grid-row:1}.mo-cell.state{grid-column:2/3;grid-row:1;justify-self:end}.mo-cell.reason{grid-column:1/-1;grid-row:2;border-top:1px solid var(--line);padding-top:6px}.mo-cell.reason .mo-sub{display:none}.mo-cell.activity{grid-column:1/2;grid-row:3}.mo-row-action{grid-column:2/3;grid-row:3;align-self:end}.mo-row details{grid-column:1/-1;grid-row:4}.mo-toolbar{align-items:flex-start;flex-direction:column}.mo-pager{align-self:stretch;justify-content:flex-end}.mo-technical-body{grid-template-columns:1fr}}
@media(max-width:640px){.mo-shell{margin:0 -18px 24px;border-left:0;border-right:0;border-radius:0}.mo-head,.mo-main{padding-left:14px;padding-right:14px}.mo-head{gap:13px}.mo-head h2{font-size:22px}.mo-head-actions{width:100%}.mo-boundary{gap:4px}.mo-refresh-control{width:100%;justify-content:space-between}.mo-refresh-state{width:auto;flex:1;text-align:left}.mo-signals>div{padding:10px 12px}.mo-signals b{font-size:15px}.mo-warning{margin-left:14px;margin-right:14px}.mo-queue-head{display:block}.mo-safe-note{text-align:left;margin-top:5px}.mo-filter{min-height:34px}.mo-row-action .mo-button{min-height:36px}.mo-technical{margin-left:14px;margin-right:14px}.mo-row-detail{grid-template-columns:1fr}.mo-row-detail .wide{grid-column:auto}}
@media(prefers-reduced-motion:reduce){.mo-shell *{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
"""


MAINTENANCE_PAGE_SIZE = 8


def _maintenance_view_state(entry: Mapping[str, Any]) -> str:
    """Map Core-owned status to a display bucket without changing eligibility."""

    if (
        bool(entry.get("remove_worktree_eligible"))
        and str(entry.get("cache_state")) == "current"
        and not bool(entry.get("is_primary_worktree"))
    ):
        return "eligible"
    if str(entry.get("cache_state", "unknown")) != "current" or str(
        entry.get("classification", "unknown")
    ) in {"legacy-unmanaged", "review-integration-pending"}:
        return "attention"
    return "protected"


def _maintenance_workspace_label(entry: Mapping[str, Any]) -> tuple[str, str]:
    if bool(entry.get("is_primary_worktree")):
        return "主工作区", workspace_classification(entry.get("classification"))
    branch = _branch_label(entry.get("branch"))
    task = branch.removeprefix("codex/")
    if task and task != "detached":
        return task, workspace_classification(entry.get("classification"))
    path = Path(str(entry.get("registered_path") or ""))
    return path.name or "待确认的工作区", workspace_classification(entry.get("classification"))


def _maintenance_activity_label(value: object) -> str:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return "最近证据待确认"
    return parsed.strftime("最近检查 %m月%d日 %H:%M")


def _maintenance_row(entry: Mapping[str, Any], *, hidden: bool, control: bool) -> str:
    view_state = _maintenance_view_state(entry)
    state_label = {
        "attention": "需要处理",
        "eligible": "可安全删除",
        "protected": "受保护",
    }[view_state]
    title, subtitle = _maintenance_workspace_label(entry)
    reasons = [str(value) for value in entry.get("reasons", [])]
    unknown = [str(value) for value in entry.get("unknown", [])]
    eligible = view_state == "eligible"
    primary_reason = maintenance_reason(reasons[0]) if reasons else (
        "证据仍需确认" if unknown else (
            "已满足当前安全删除条件" if eligible else "当前证据没有给出可安全删除结论"
        )
    )
    action = (
        '<button class="mo-button danger" type="button" data-maintenance-preflight="%s">安全删除</button>'
        % _esc(entry.get("workspace_id"))
        if eligible and control
        else '<span class="mo-sub">%s</span>' % (
            "主工作区保留" if bool(entry.get("is_primary_worktree")) else (
                "请使用本机动态入口" if eligible else "暂无删除操作"
            )
        )
    )
    technical_reasons = " · ".join(reasons) or "no-machine-reason"
    technical_unknown = " · ".join(unknown) or "none"
    return (
        '<div class="mo-row" role="row" data-maintenance-workspace="%s" '
        'data-maintenance-view-state="%s"%s><div class="mo-row-grid">'
        '<div class="mo-cell workspace" role="cell"><b>%s</b><span class="mo-sub">%s</span></div>'
        '<div class="mo-cell state" role="cell"><span class="mo-row-state">%s</span></div>'
        '<div class="mo-cell reason" role="cell"><b>%s</b><span class="mo-sub">%s</span></div>'
        '<div class="mo-cell activity" role="cell"><time>%s</time><span class="mo-sub">%s</span></div>'
        '<div class="mo-cell mo-row-action" role="cell">%s</div>'
        '<details><summary>%s</summary><dl class="mo-row-detail">'
        '<div><dt>workspace_id</dt><dd>%s</dd></div><div><dt>branch</dt><dd>%s</dd></div>'
        '<div class="wide"><dt>registered_path</dt><dd>%s</dd></div>'
        '<div><dt>HEAD</dt><dd>%s</dd></div><div><dt>cache_state</dt><dd>%s</dd></div>'
        '<div class="wide"><dt>reasons</dt><dd>%s</dd></div>'
        '<div class="wide"><dt>unknown / secondary evidence</dt><dd>%s</dd></div>'
        '</dl></details></div></div>'
        % (
            _esc(entry.get("workspace_id")),
            view_state,
            " hidden" if hidden else "",
            _esc(title),
            _esc(subtitle),
            state_label,
            _esc(primary_reason),
            "最新资格来自 Maintenance Core" if eligible else "完整原因见行内详情",
            _esc(_maintenance_activity_label(entry.get("scanned_at"))),
            _esc(display_status(entry.get("cache_state", "unknown"))),
            action,
            TECHNICAL_DETAILS_LABEL,
            _esc(entry.get("workspace_id")),
            _esc(entry.get("branch") or "detached"),
            _esc(entry.get("registered_path")),
            _esc(entry.get("head") or "Unknown"),
            _esc(entry.get("cache_state", "unknown")),
            _esc(technical_reasons),
            _esc(technical_unknown),
        )
    )


def _maintenance_panel(projection: Mapping[str, Any]) -> str:
    maintenance = projection.get("maintenance")
    if not isinstance(maintenance, Mapping):
        maintenance = {}
    control = bool(maintenance.get("control_available"))
    last = maintenance.get("last_run") if isinstance(maintenance.get("last_run"), Mapping) else {}
    counts = last.get("counts") if isinstance(last.get("counts"), Mapping) else {}
    cache = maintenance.get("cache") if isinstance(maintenance.get("cache"), Mapping) else {}
    cache_entries = [item for item in cache.get("entries", []) if isinstance(item, Mapping)]
    eligible_entries = [
        entry for entry in cache_entries
        if bool(entry.get("remove_worktree_eligible"))
        and str(entry.get("cache_state")) == "current"
        and not bool(entry.get("is_primary_worktree"))
    ]
    view_counts = Counter(_maintenance_view_state(entry) for entry in cache_entries)
    default_filter = (
        "attention" if view_counts["attention"] else
        "eligible" if view_counts["eligible"] else
        "protected"
    )
    state_order = {"attention": 0, "eligible": 1, "protected": 2}
    ordered_entries = sorted(
        cache_entries,
        key=lambda entry: (
            state_order[_maintenance_view_state(entry)],
            _maintenance_workspace_label(entry)[0].casefold(),
            str(entry.get("workspace_id", "")),
        ),
    )
    initial_index = 0
    rows = []
    for entry in ordered_entries:
        matches_default = _maintenance_view_state(entry) == default_filter
        hidden = not matches_default or initial_index >= MAINTENANCE_PAGE_SIZE
        rows.append(_maintenance_row(entry, hidden=hidden, control=control))
        if matches_default:
            initial_index += 1
    queue_html = "".join(rows) or '<div class="mo-empty mo-table-empty">缓存尚未建立；刷新后才会显示工作区状态。</div>'
    protected = maintenance.get("protected_reasons") if isinstance(maintenance.get("protected_reasons"), Mapping) else {}
    protected_html = "".join('<div class="mo-reason"><span>%s</span><b>%s</b><details><summary>%s</summary><code>%s</code></details></div>' % (_esc(maintenance_reason(reason)), _esc(count), TECHNICAL_DETAILS_LABEL, _esc(reason)) for reason, count in sorted(protected.items())) or '<div class="mo-empty">没有已记录的受保护原因；未扫描不等于可清理。</div>'
    policy = maintenance.get("policy") if isinstance(maintenance.get("policy"), Mapping) else {}
    policy_html = "".join('<span>%s</span><b>%s</b>' % (_esc(key), _esc(value)) for key, value in policy.items() if key != "ignored_allowlist")
    receipts = [item for item in maintenance.get("receipts", []) if isinstance(item, Mapping)]
    branch_reminders = [item for item in maintenance.get("local_branch_reminders", []) if isinstance(item, Mapping)]
    background = maintenance.get("background_refresh") if isinstance(maintenance.get("background_refresh"), Mapping) else {}
    background_status = str(background.get("status", "idle"))
    api_base = str(maintenance.get("api_base", "/team/api/maintenance"))
    history_html = "".join('<div class="mo-reason"><span>%s</span><b>%s</b></div>' % (_esc(item.get("receipt_id")), _esc(item.get("outcome"))) for item in receipts[-8:]) or '<div class="mo-empty">尚无执行记录。</div>'
    warnings = [
        item for item in maintenance.get("historical_evidence_warnings", [])
        if isinstance(item, Mapping)
    ]
    historical_warning = (
        '<details class="mo-warning" data-maintenance-historical-warning><summary>历史记录需要确认 · 展开技术详情</summary>'
        '<p>旧记录已原样保留为历史证据；不阻止当前刷新，也不放宽当前安全删除条件。</p>'
        '<code>%s</code></details>'
        % _esc(" · ".join(str(item.get("message")) for item in warnings))
        if warnings else ""
    )
    leading_reasons = "、".join(maintenance_reason(reason) for reason in list(sorted(protected))[:3])
    safe_note = (
        '<span data-maintenance-quick-empty>目前没有可安全删除项。%s</span>'
        % ("主要保护原因：" + _esc(leading_reasons) + "。" if leading_reasons else "尚未取得足够的当前证据。")
        if not eligible_entries else
        '<span data-maintenance-quick-empty>只有合格行提供“安全删除”；点击后仍执行最新预检与二次确认。</span>'
    )
    default_count = int(view_counts[default_filter])
    default_pages = max(1, (default_count + MAINTENANCE_PAGE_SIZE - 1) // MAINTENANCE_PAGE_SIZE)
    return (
        '<article class="page wide" id="workspace-maintenance" data-kind="workspace-maintenance" data-title="工作区维护" data-maintenance-control="%s" data-maintenance-api-base="%s" data-maintenance-refresh-path="%s" data-maintenance-remove-path="%s" data-maintenance-reload-after-action="%s" data-maintenance-page-size="%s" data-maintenance-default-filter="%s">'
        '<section class="mo-shell"><header class="mo-head"><div><span class="mo-kicker">工作区维护 · 仅限本机</span><h2>工作区维护</h2><p>先看需要处理、可以安全删除和仍受保护的工作区；发现建议不会自动执行。</p></div>'
        '<div class="mo-head-actions"><div class="mo-boundary" aria-label="运行边界"><span class="current">当前证据</span><span>零外部网络</span><span>分支保留</span></div>'
        '<div class="mo-refresh-control"><span class="mo-refresh-state" role="status" aria-live="polite" data-maintenance-notice>%s</span><button class="mo-button" type="button" data-maintenance-scan%s>刷新工作区状态</button></div></div></header>'
        '<div class="mo-progress %s" aria-hidden="true"></div>'
        '<div class="mo-signals"><div><small>全部工作区</small><b data-maintenance-worktrees>%s</b></div><div class="attention"><small>需要处理</small><b data-maintenance-attention-count>%s</b></div><div class="safe"><small>可安全删除</small><b data-maintenance-eligible-count>%s</b></div><div><small>受保护</small><b data-maintenance-protected-count>%s</b></div></div>%s'
        '<main class="mo-main"><div class="mo-queue-head"><div><h3>工作区队列</h3><p>稳定分组 · 每页最多 %s 项 · 点击“详情”查看完整技术证据</p></div><div class="mo-safe-note"><b>可安全删除 %s 项</b><br>%s</div></div>'
        '<div class="mo-toolbar"><div class="mo-filters" role="group" aria-label="工作区状态筛选">'
        '<button class="mo-filter" type="button" data-maintenance-filter="attention" aria-pressed="%s">需要处理 %s</button>'
        '<button class="mo-filter" type="button" data-maintenance-filter="eligible" aria-pressed="%s">可安全删除 %s</button>'
        '<button class="mo-filter" type="button" data-maintenance-filter="protected" aria-pressed="%s">受保护 %s</button>'
        '<button class="mo-filter" type="button" data-maintenance-filter="all" aria-pressed="%s">全部 %s</button></div>'
        '<div class="mo-pager" aria-label="工作区分页"><button type="button" data-maintenance-page="previous" aria-label="上一页" disabled>‹</button><span data-maintenance-page-status>第 1 / %s 页</span><button type="button" data-maintenance-page="next" aria-label="下一页"%s>›</button></div></div>'
        '<div class="mo-table" role="table" aria-label="工作区维护列表"><div class="mo-table-head" role="row"><span>工作区 / 关联任务</span><span>状态</span><span>主要原因</span><span>最近证据</span><span>操作</span></div><div data-maintenance-queue>%s</div><div class="mo-empty mo-table-empty" data-maintenance-filter-empty hidden>当前筛选没有工作区。</div></div></main>'
        '<details class="mo-technical"><summary>技术策略详情</summary><div class="mo-technical-body">'
        '<section><h4>策略与阈值</h4><div class="mo-policy">%s</div></section>'
        '<section><h4>主要保护原因</h4><div data-maintenance-protected>%s</div></section>'
        '<section><h4>本机操作边界</h4><div class="mo-boundaries"><div><b>工作区</b><span>仅在证据绑定、本机确认后移除</span></div><div><b>本地分支</b><span>%s 个到期提醒；当前不删除</span></div><div><b>远端分支</b><span>个人模式不观察、不删除</span></div><div><b>定时刷新</b><span>无定时任务；页面关闭后不会运行</span></div></div><details class="mo-history"><summary>授权与执行历史</summary>%s</details></section>'
        '</div></details></section></article>'
        % (
            "true" if control else "false", _esc(api_base), _esc(maintenance.get("refresh_path", "/scan")), _esc(maintenance.get("remove_path", "/quick-remove")), "true" if maintenance.get("reload_after_action", True) else "false", MAINTENANCE_PAGE_SIZE, default_filter,
            _esc(display_status(background_status)), "" if control else " disabled",
            "running" if background_status in {"pending", "running"} else "",
            _esc(len(cache_entries) if cache_entries else counts.get("worktrees", "待确认")), _esc(view_counts["attention"]), _esc(view_counts["eligible"]), _esc(view_counts["protected"]), historical_warning,
            MAINTENANCE_PAGE_SIZE, _esc(len(eligible_entries)), safe_note,
            "true" if default_filter == "attention" else "false", _esc(view_counts["attention"]),
            "true" if default_filter == "eligible" else "false", _esc(view_counts["eligible"]),
            "true" if default_filter == "protected" else "false", _esc(view_counts["protected"]),
            "false", _esc(len(cache_entries)), default_pages, " disabled" if default_pages <= 1 else "",
            queue_html, policy_html, protected_html, _esc(len(branch_reminders)), history_html,
        )
    )


MAINTENANCE_OBSERVATORY_JS = r"""
(function(){
 const page=document.getElementById('workspace-maintenance');if(!page||page.dataset.maintenanceControl!=='true')return;
 const notice=page.querySelector('[data-maintenance-notice]');
 const base=page.dataset.maintenanceApiBase;
 const refreshPath=page.dataset.maintenanceRefreshPath||'/scan';
 const removePath=page.dataset.maintenanceRemovePath||'/quick-remove';
 const reloadAfterAction=page.dataset.maintenanceReloadAfterAction!=='false';
 const pageSize=Number(page.dataset.maintenancePageSize)||8;
 let activeFilter=page.dataset.maintenanceDefaultFilter||'attention',currentPage=1;
 const reasonLabel=(value)=>({'workspace-path-not-found':'工作区路径不存在','workspace-path-boundary-not-safe':'工作区路径不在安全边界内','legacy-or-unknown-workspace-requires-explicit-adoption':'历史或待确认工作区尚未明确接管','workstream-is-active':'任务仍在进行','review-or-integration-is-pending':'审查或集成尚未完成','workspace-is-protected-or-retained':'工作区受保护或已明确保留','git-identity-or-common-dir-not-verified':'Git 身份或公共目录尚未验证','tracked-worktree-changes-present':'存在已跟踪但未提交的改动','unknown-untracked-paths-present':'存在待确认的未跟踪文件','unknown-or-sensitive-ignored-paths-present':'存在待确认或敏感的忽略文件','git-private-closure-record-missing':'缺少 Git 私有区关闭记录','review-package-evidence-missing':'缺少审查包证据','passed-validation-evidence-missing':'缺少已通过的验证证据','review-decision-evidence-missing':'缺少审查决定证据','closure-validation-references-missing':'关闭记录缺少验证引用','unique-commit-check-failed':'无法确认是否存在独有提交','workspace-has-commits-not-reachable-from-integration-oid':'工作区仍有未进入集成目标的提交','workstream-session-is-not-integrated-or-closed':'任务尚未集成并关闭','integrated-grace-period-active':'集成后的保护期尚未结束'}[value]||'其他保护原因（见技术详情）');
 async function api(path,body){const response=await fetch(base+path,{method:'POST',headers:{'Accept':'application/json','Content-Type':'application/json'},body:JSON.stringify(body||{})});const value=await response.json();if(!response.ok)throw new Error(value.error||'本机维护操作失败');return value}
 async function status(){const response=await fetch(base+'/status',{headers:{'Accept':'application/json'}});const value=await response.json();if(!response.ok)throw new Error(value.error||'状态读取失败');return value}
 const shownState=(value)=>({current:'当前',stale:'历史状态',unknown:'待确认',idle:'空闲',pending:'等待刷新',running:'正在刷新',succeeded:'刷新完成',failed:'刷新失败','timed-out':'刷新超时'}[value]||value||'待确认');
 const classificationLabel=(value)=>({'registered-active':'进行中的工作区','review-integration-pending':'等待审查或集成','integrated-closed':'已集成并关闭','legacy-unmanaged':'历史或待接管','protected-retained':'明确保留','primary-worktree':'主工作区'}[value]||'状态待确认');
 const viewState=(entry)=>entry.remove_worktree_eligible&&entry.cache_state==='current'&&!entry.is_primary_worktree?'eligible':(entry.cache_state!=='current'||['legacy-unmanaged','review-integration-pending'].includes(entry.classification)?'attention':'protected');
 const workspaceLabel=(entry)=>{if(entry.is_primary_worktree)return'主工作区';const branch=String(entry.branch||'').replace(/^refs\/heads\//,'').replace(/^codex\//,'');if(branch)return branch;const parts=String(entry.registered_path||'').split(/[\\/]/);return parts.pop()||'待确认的工作区'};
 const activityLabel=(value)=>{const date=new Date(value);return Number.isNaN(date.getTime())?'最近证据待确认':'最近检查 '+new Intl.DateTimeFormat('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(date)};
 function textCell(kind,strong,sub){const cell=document.createElement('div');cell.className='mo-cell '+kind;cell.setAttribute('role','cell');const first=document.createElement(strong?'b':'span');first.textContent=strong||sub||'';cell.append(first);if(strong&&sub){const second=document.createElement('span');second.className='mo-sub';second.textContent=sub;cell.append(second)}return cell}
 function detailItem(term,value,wide=false){const wrap=document.createElement('div');if(wide)wrap.className='wide';const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=term;dd.textContent=value;wrap.append(dt,dd);return wrap}
 function buildRow(entry){const state=viewState(entry),reasons=entry.reasons||[],unknown=entry.unknown||[];const row=document.createElement('div');row.className='mo-row';row.setAttribute('role','row');row.dataset.maintenanceWorkspace=entry.workspace_id;row.dataset.maintenanceViewState=state;const grid=document.createElement('div');grid.className='mo-row-grid';grid.append(textCell('workspace',workspaceLabel(entry),classificationLabel(entry.classification)));const statusCell=textCell('state',null,null),pill=document.createElement('span');pill.className='mo-row-state';pill.textContent={attention:'需要处理',eligible:'可安全删除',protected:'受保护'}[state];statusCell.append(pill);grid.append(statusCell);const primary=reasons.length?reasonLabel(reasons[0]):(unknown.length?'证据仍需确认':(state==='eligible'?'已满足当前安全删除条件':'当前证据没有给出可安全删除结论'));grid.append(textCell('reason',primary,state==='eligible'?'最新资格来自 Maintenance Core':'完整原因见行内详情'));grid.append(textCell('activity',activityLabel(entry.scanned_at),shownState(entry.cache_state)));const action=document.createElement('div');action.className='mo-cell mo-row-action';action.setAttribute('role','cell');if(state==='eligible'){const button=document.createElement('button');button.className='mo-button danger';button.type='button';button.dataset.maintenancePreflight=entry.workspace_id;button.textContent='安全删除';action.append(button)}else{const label=document.createElement('span');label.className='mo-sub';label.textContent=entry.is_primary_worktree?'主工作区保留':'暂无删除操作';action.append(label)}grid.append(action);const details=document.createElement('details'),summary=document.createElement('summary'),dl=document.createElement('dl');summary.textContent='技术详情';dl.className='mo-row-detail';dl.append(detailItem('workspace_id',entry.workspace_id||''),detailItem('branch',entry.branch||'detached'),detailItem('registered_path',entry.registered_path||'',true),detailItem('HEAD',entry.head||'Unknown'),detailItem('cache_state',entry.cache_state||'unknown'),detailItem('reasons',reasons.join(' · ')||'no-machine-reason',true),detailItem('unknown / secondary evidence',unknown.join(' · ')||'none',true));details.append(summary,dl);grid.append(details);row.append(grid);return row}
 function rows(){return Array.from(page.querySelectorAll('[data-maintenance-queue] .mo-row'))}
 function refreshSummary(){const values=rows(),counts={attention:0,eligible:0,protected:0};values.forEach(row=>counts[row.dataset.maintenanceViewState]++);const set=(selector,value)=>{const node=page.querySelector(selector);if(node)node.textContent=value};set('[data-maintenance-worktrees]',values.length);set('[data-maintenance-attention-count]',counts.attention);set('[data-maintenance-eligible-count]',counts.eligible);set('[data-maintenance-protected-count]',counts.protected);page.querySelectorAll('[data-maintenance-filter]').forEach(button=>{const key=button.dataset.maintenanceFilter,labels={attention:'需要处理',eligible:'可安全删除',protected:'受保护',all:'全部'};button.textContent=labels[key]+' '+(key==='all'?values.length:counts[key])});const quick=page.querySelector('[data-maintenance-quick-empty]');if(quick)quick.textContent=counts.eligible?'只有合格行提供“安全删除”；点击后仍执行最新预检与二次确认。':'目前没有可安全删除项。主要保护原因见技术详情。'}
 function applyTable(reset=false){if(reset)currentPage=1;const values=rows(),matches=values.filter(row=>activeFilter==='all'||row.dataset.maintenanceViewState===activeFilter),pages=Math.max(1,Math.ceil(matches.length/pageSize));currentPage=Math.min(Math.max(1,currentPage),pages);values.forEach(row=>row.hidden=true);matches.slice((currentPage-1)*pageSize,currentPage*pageSize).forEach(row=>row.hidden=false);page.querySelectorAll('[data-maintenance-filter]').forEach(button=>button.setAttribute('aria-pressed',button.dataset.maintenanceFilter===activeFilter?'true':'false'));const statusNode=page.querySelector('[data-maintenance-page-status]');if(statusNode)statusNode.textContent='第 '+currentPage+' / '+pages+' 页';const previous=page.querySelector('[data-maintenance-page="previous"]'),next=page.querySelector('[data-maintenance-page="next"]');if(previous)previous.disabled=currentPage<=1;if(next)next.disabled=currentPage>=pages;const empty=page.querySelector('[data-maintenance-filter-empty]');if(empty)empty.hidden=matches.length!==0}
 function renderMaintenance(maintenance){const entries=(maintenance.cache||{}).entries||[],root=page.querySelector('[data-maintenance-queue]');if(root){root.replaceChildren();entries.sort((left,right)=>{const order={attention:0,eligible:1,protected:2};return order[viewState(left)]-order[viewState(right)]||workspaceLabel(left).localeCompare(workspaceLabel(right),'zh-CN')}).forEach(entry=>root.append(buildRow(entry)))}refreshSummary();applyTable(true)}
 async function waitForRefresh(){for(let attempt=0;attempt<120;attempt++){const value=await status();const state=value.maintenance.background_refresh.status;if(!['pending','running'].includes(state))return value.maintenance;await new Promise(resolve=>setTimeout(resolve,500))}return{background_refresh:{status:'timed-out'},cache:{entries:[]}}}
 page.addEventListener('click',async(event)=>{const button=event.target.closest('button');if(!button)return;
   if(button.dataset.maintenanceFilter){activeFilter=button.dataset.maintenanceFilter;applyTable(true);return}
   if(button.dataset.maintenancePage){currentPage+=button.dataset.maintenancePage==='next'?1:-1;applyTable();return}
   if(!button.hasAttribute('data-maintenance-scan')&&!button.dataset.maintenancePreflight)return;
   button.disabled=true;notice.className='mo-refresh-state';
   try{
    if(button.hasAttribute('data-maintenance-scan')){const progress=page.querySelector('.mo-progress');if(progress)progress.classList.add('running');notice.textContent='正在刷新…';await api(refreshPath,{});const maintenance=await waitForRefresh();const state=maintenance.background_refresh.status;notice.textContent=shownState(state);if(progress)progress.classList.remove('running');if(reloadAfterAction){window.location.reload();return}renderMaintenance(maintenance);button.disabled=false;return}
    if(button.dataset.maintenancePreflight){notice.textContent='正在最新预检…';const value=await api('/preflight',{target_id:button.dataset.maintenancePreflight});const result=value.preflight;if(!result.eligible){throw new Error('目标受保护：'+(result.reasons||result.unknown||['证据不足']).map(reasonLabel).join(' · '))}if(!window.confirm('只删除工作区，保留分支和提交。确认移除这个工作区？')){button.disabled=false;notice.textContent='已取消';return}notice.textContent='正在安全删除…';const removed=await api(removePath,{item_id:result.item.item_id});if(removed.receipt.outcome!=='verified')throw new Error('安全删除未完成：'+removed.receipt.outcome);notice.textContent='已删除工作区；分支已保留';if(reloadAfterAction){window.location.reload();return}const row=button.closest('[data-maintenance-workspace]');if(row)row.remove();refreshSummary();applyTable();return}
   }catch(error){const progress=page.querySelector('.mo-progress');if(progress)progress.classList.remove('running');notice.className='mo-refresh-state error';notice.textContent=error.message;button.disabled=false}});
 refreshSummary();applyTable();
})();
"""


def render_maintenance_control_document(
    maintenance: Mapping[str, Any],
    *,
    api_base: str = "/control/api/maintenance",
) -> str:
    """Render the cache-first root-only Maintenance console without a W3 page scan."""
    projection = dict(maintenance)
    projection["control_available"] = True
    projection["api_base"] = api_base
    panel = _maintenance_panel({"maintenance": projection})
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Orrery · 工作区维护</title><style>
:root{color-scheme:dark;--bg:#101516;--bg2:#151c1e;--bg3:#1c2527;--fg:#edf4f1;--mut:#91a19c;--line:#2d3a3b;--acc:#63d6cf}
*{box-sizing:border-box}html,body{margin:0;min-width:0;background:var(--bg);color:var(--fg);font-family:"IBM Plex Sans","Segoe UI",sans-serif}body{padding:28px}.control-mast{max-width:1180px;margin:0 auto 14px;display:flex;justify-content:space-between;gap:18px;align-items:end}.control-mast small{color:var(--acc);font:700 10px/1.3 "Cascadia Code",Consolas,monospace;letter-spacing:.12em}.control-mast h1{margin:5px 0 0;font-size:18px}.control-mast span{color:var(--mut);font-size:10px}.control-wrap{max-width:1180px;margin:auto}.page{display:block!important}.page.wide{max-width:none}.mo-shell{box-shadow:0 18px 55px rgba(0,0,0,.2)}button:focus-visible{outline:2px solid var(--acc);outline-offset:2px}@media(max-width:640px){body{padding:12px}.control-mast{align-items:start;flex-direction:column}.control-wrap{margin:0 -12px}.control-wrap .mo-shell{margin:0}}
""" + MAINTENANCE_OBSERVATORY_CSS + """</style></head><body><header class="control-mast"><div><small>ORRERY / 本机控制</small><h1>工作区维护控制台</h1></div><span>127.0.0.1 · 仅项目根 · 零外部网络</span></header><main class="control-wrap">""" + panel + """</main><script>""" + MAINTENANCE_OBSERVATORY_JS + """</script></body></html>"""


def render_personal_observatory_panel(projection: Mapping[str, Any]) -> str:
    if projection.get("contract_type") == "orrery-active-task-projection-v1":
        from .active_task_projection import render_active_task_panel

        return render_active_task_panel(
            projection,
            dynamic=projection.get("dynamic") is True,
        )
    if projection.get("status") != "ready":
        error = projection.get("error", {})
        return (
            '<article class="page wide" id="personal-observatory" data-kind="personal-observatory" '
            'data-title="个人工作台" data-status="unavailable" data-read-only="true">'
            '<section class="po-shell"><div class="po-brief"><span class="po-kicker">个人工作台</span>'
            '<h2>项目态势暂不可用</h2><p>当前无法读取完整的本机项目状态。</p>'
            '<details><summary>技术详情</summary><code>%s: %s</code></details>'
            '<span class="po-lock">只读 · 零外部网络</span></div></section></article>'
            % (_esc(error.get("type", "Unknown")), _esc(error.get("message", "Unknown")))
        )
    current = projection.get("current") or {}
    health = projection.get("health")
    if not isinstance(health, Mapping):
        health = _derive_health_projection(
            projection.get("workstreams", []),
            projection.get("findings", []),
            projection.get("w3_evidence")
            if isinstance(projection.get("w3_evidence"), Mapping)
            else None,
        )
    w3_labels = {
        "review_queue": "审查队列",
        "integration_eligibility": "集成资格",
        "cleanup_eligibility": "清理资格",
    }
    w3_rows = "".join(
        '<div class="po-w3-row" data-w3-slot="%s"><b>%s</b><span class="po-scope %s">%s</span>'
        '<small>%s</small></div>'
        % (
            _esc(key),
            _esc(w3_labels[key]),
            _esc(_status_class(projection["w3"][key]["status"])),
            _esc(display_status(projection["w3"][key]["status"])),
            _esc(projection["w3"][key]["detail"]),
        )
        for key in W3_SLOT_KEYS
    )
    w3_evidence = projection.get("w3_evidence")
    w3_evidence_html = _w3_evidence_html(
        w3_evidence if isinstance(w3_evidence, Mapping) else None
    )
    active_cards = [
        card for card in projection["workstreams"]
        if card.get("display_group") == "active"
    ]
    visible_ids = {
        str(card.get("workstream_id")) for card in projection.get("workstreams", [])
    }
    lineage_rows = "".join(
        '<div class="po-inventory-row" data-lineage-status="%s"><div><b>%s</b>'
        '<span>%s</span></div><code>%s</code><span>%s</span><span>继承 %s 条路径</span></div>'
        % (
            _esc(item.get("status", "unknown")),
            _esc(item.get("workstream_id", "Unknown")),
            _esc("接续自 " + str(item.get("base_workstream_id", "Unknown"))),
            _esc(_short_oid(item.get("task_base_oid"))),
            _esc({"parent-unavailable-unknown": "上游任务待确认", "current": "当前"}.get(str(item.get("status")), "待确认")),
            _esc(item.get("inherited_path_count", 0)),
        )
        for item in projection.get("lineage_summaries", [])
        if item.get("base_workstream_id") and item.get("workstream_id") in visible_ids
    )
    lineage_member_ids = {
        str(value)
        for item in projection.get("lineage_summaries", [])
        if item.get("base_workstream_id") and item.get("workstream_id") in visible_ids
        for value in (item.get("workstream_id"), item.get("base_workstream_id"))
        if value
    }
    chain_finding_ids = {
        item.get("finding_id")
        for item in projection.get("findings", [])
        if item.get("finding_id")
        and set(map(str, item.get("workstream_ids", []))).issubset(lineage_member_ids)
    }
    lineage_panel = (
        '<details class="po-vault po-lineage-chain"><summary><div><b>接续任务链</b>'
        '<span>精确任务基点；继承路径不计作冲突发现</span></div>'
        '<span>%s 个任务链内独立发现</span></summary><div class="po-vault-body">%s</div></details>'
        % (len(chain_finding_ids), lineage_rows)
        if lineage_rows
        else ""
    )
    inventory_cards = [
        card for card in projection["workstreams"]
        if card.get("display_group") != "active"
    ]
    workstreams = lineage_panel + "".join(_workstream_card(card) for card in active_cards)
    if not workstreams:
        workstreams = (
            '<div class="po-empty" data-state="no-worktree">目前没有可确认的进行中任务</div>'
        )
    inventory = ""
    if inventory_cards:
        inventory = (
            '<details class="po-inventory"><summary>本机可见工作区 · %d（非活动项，按需查看）</summary>'
            '<div class="po-inventory-body">%s</div></details>'
            % (
                len(inventory_cards),
                "".join(_worktree_inventory_row(card) for card in inventory_cards),
            )
        )
    subsystems = "".join(
        '<div class="po-subsystem"><div><b>%s</b><span>%d 个未结束任务</span></div>'
        '<code>%s</code></div>'
        % (
            _esc(item["subsystem_id"]),
            len(item["workstream_ids"]),
            _esc(" · ".join(item["workstream_ids"])),
        )
        for item in projection["subsystems"]
    ) or '<div class="po-empty" data-state="no-subsystem">目前没有任务关联到项目模块</div>'
    delivery_health = health["delivery_now"]
    reconciliation_health = health["reconciliation"]
    hygiene_health = health["workspace_hygiene"]
    unknown_health = health["unknown_accounting"]
    direct_count = int(delivery_health["current_blocker_count"])
    running_count = sum(
        card.get("runtime_condition") == "active" for card in active_cards
    )
    paused_count = sum(
        card.get("runtime_condition") in {"paused", "waiting-for-user"}
        for card in active_cards
    )
    blocked_count = sum(
        card.get("runtime_condition") in {"blocked-by-conflict", "failed", "offline"}
        for card in active_cards
    )
    stale_count = sum(
        card.get("evidence_freshness") != "current" for card in active_cards
    )
    focus = current if current.get("display_group") == "active" else (
        active_cards[0] if active_cards else None
    )
    if current.get("display_group") == "candidate-unregistered":
        project_summary = (
            "当前候选尚未登记任务，无法判断交付资格；请先登记任务并生成或绑定审查包。"
        )
    elif current.get("display_group") == "protected-primary":
        project_summary = (
            "当前目录是受保护的主工作区，只用于集成，不计作普通 Agent 任务。"
        )
    elif focus:
        project_summary = (
            "当前 %s 正在推进 %s，处于%s。"
            % (
                focus.get("workstream_id", "待确认任务"),
                focus.get("primary_subsystem_id", "待确认模块"),
                _human_phase(focus.get("lifecycle_phase", "unavailable")),
            )
        )
        if focus.get("runtime_condition") != "active":
            project_summary += " 运行状态为%s。" % _human_runtime(
                focus.get("runtime_condition", "stale-unknown")
            )
        if len(active_cards) > 1:
            project_summary += " 本机还有 %d 个未结束任务。" % (
                len(active_cards) - 1
            )
    else:
        project_summary = "本机没有可确认的未结束任务；远端和未上报工作不在当前观察范围内。"

    priorities: list[tuple[str, str, str]] = []
    if direct_count:
        priorities.append((
            "critical",
            "%d 个确定的直接重叠需要处理" % direct_count,
            "这些是 W1/W2 已证明的路径或独占面重叠，不是推测。",
        ))
    if blocked_count or paused_count:
        priorities.append((
            "warning",
            "%d 个任务没有处于持续执行状态" % (blocked_count + paused_count),
            "%d 个阻塞／失败／离线，%d 个暂停或等待确认。" % (
                blocked_count,
                paused_count,
            ),
        ))
    if reconciliation_health["total"]:
        priorities.append((
            "warning",
            "%d 项待确认的任务／历史状态" % reconciliation_health["total"],
            "%d 个状态已过期的任务登记，%d 个历史重叠，%d 个过期审查包，%d 个未登记候选。"
            % (
                reconciliation_health["stale_session_count"],
                reconciliation_health["finding_count"],
                reconciliation_health["stale_review_count"],
                reconciliation_health["unregistered_candidate_count"],
            ),
        ))
    if isinstance(w3_evidence, Mapping):
        pending_reviews = [
            item for item in w3_evidence.get("review_queue", [])
            if item.get("queue_status") == "pending"
        ]
        approval_needed = sum(
            item.get("human_approval", {}).get("count", 0)
            < item.get("human_approval", {}).get("required", 1)
            for item in pending_reviews
        )
        eligible_reviews = sum(
            item.get("integration", {}).get("eligible") is True
            for item in pending_reviews
        )
        cleanup_ready = sum(
            item.get("eligible") is True for item in w3_evidence.get("cleanup", [])
        )
        if approval_needed:
            priorities.append((
                "warning",
                "%d 个审查包仍需人工批准" % approval_needed,
                "风险等级、所需能力与非作者要求均来自 W3 核心契约。",
            ))
        if eligible_reviews:
            priorities.append((
                "warning",
                "%d 个候选满足当前集成资格" % eligible_reviews,
                "这只表示 W3 核心门禁通过；集成引用仍未更新。",
            ))
        if cleanup_ready:
            priorities.append((
                "warning",
                "%d 个工作区满足清理资格" % cleanup_ready,
                "四类动作仍需分别授权，当前全部 performed=false。",
            ))
    if all(slot.get("status") == "unavailable" for slot in projection["w3"].values()):
        priorities.append((
            "unknown",
            "当前不能判断审查、集成和清理资格",
            "W3 数据来源缺失、失败或格式不受支持；已保持安全降级。",
        ))
    if hygiene_health["debt_count"] or hygiene_health["no_session"]:
        priorities.append((
            "unknown",
            "%d 个工作区需要清理建议" % hygiene_health["debt_count"],
            "%d 个缺少任务登记，%d 个已明确保留；这些不计入当前直接阻断。"
            % (hygiene_health["no_session"], hygiene_health["retained"]),
        ))
    if unknown_health["total"]:
        priorities.append((
            "unknown",
            "%d 项证据不足状态已完整保留" % unknown_health["total"],
            "其中 %d 项归入待确认的任务／历史状态，%d 项归入工作区清理建议；没有静默丢弃。"
            % (unknown_health["reconciliation"], unknown_health["hygiene"]),
        ))
    if not priorities:
        priorities.append((
            "unknown",
            "本机没有明确告警",
            "个人模式不观察远端，因此不能据此表达为全局零风险。",
        ))
    priority_html = "".join(
        '<li class="%s"><span class="po-priority-mark"></span><div><b>%s</b><p>%s</p></div></li>'
        % (_esc(severity), _esc(title), _esc(detail))
        for severity, title, detail in priorities
    )
    return (
        '<article class="page wide" id="personal-observatory" data-kind="personal-observatory" '
        'data-title="个人工作台" data-status="ready" data-read-only="true">'
        '<section class="po-shell" data-mode="personal" data-network-performed="false">'
        '<section class="po-brief" data-zone="project-status"><div class="po-brief-top">'
        '<div><span class="po-kicker">个人工作台 · 派生只读视图</span>'
        '<h2>交付状态</h2><p>%s</p></div>'
        '<span class="po-lock">只读 · 零外部网络</span></div>'
        '<div class="po-brief-grid"><div class="po-signals">'
        '<div><b>%d</b><span>当前交付任务</span></div>'
        '<div class="%s"><b>%d</b><span>当前直接阻断</span></div>'
        '<div><b>%d</b><span>待确认的任务／历史状态</span></div><div><b>%d</b><span>工作区清理建议</span></div>'
        '</div><aside class="po-proof"><div><small>本机范围</small><b>%d 个工作区</b></div>'
        '<div><small>趋势</small><b>暂无历史快照</b></div><div><small>交付资格</small><b>%s</b></div>'
        '<div><small>采集时间</small><code>%s</code></div></aside></div></section>'
        '<section class="po-zone" data-zone="attention"><div class="po-zone-head"><h3>当前阻断／待确认的任务与历史状态／工作区清理建议</h3>'
        '<span>三类状态互不重复；证据不足会明确保留</span></div><p class="po-empty">待确认项用于追踪任务和历史证据；清理建议用于整理本机工作区，不代表可以自动删除。</p><ol class="po-priorities">%s</ol></section>'
        '<section class="po-zone" data-zone="workstreams"><div class="po-zone-head"><h3>谁在推进什么</h3>'
        '<span>仅显示尚未集成或关闭的任务；点击行查看技术证据</span></div>'
        '<div class="po-workstreams">%s</div></section>'
        '<details class="po-vault" data-zone="subsystems"><summary><div><b>影响到哪里</b>'
        '<span>模块 ID 来自任务声明，仅在技术详情中显示</span></div><span>展开技术详情</span></summary><div class="po-vault-body"><div class="po-subsystems">%s</div></div></details>'
        '<details class="po-vault"><summary><div><b>技术证据</b><span>Git、W3 显示槽与本机工作区清单</span></div>'
        '<span>按需展开</span></summary><div class="po-vault-body"><section><h4>W3 状态</h4><div class="po-w3">%s</div></section>%s%s</div></details>'
        '<div class="po-foot"><span>采集于 %s</span><span>个人工作台投影 · 未写作者文档 · 未访问网络 · 团队模式关闭</span>'
        '<details><summary>技术详情</summary><code>%s</code></details></div>'
        '</section></article>'
        % (
            _esc(project_summary),
            delivery_health["workstream_count"],
            "critical" if direct_count else "",
            direct_count,
            reconciliation_health["total"],
            hygiene_health["debt_count"],
            len(projection["workstreams"]),
            _esc(display_status(projection["w3"]["integration_eligibility"]["status"])),
            _esc(projection["captured_at"]),
            priority_html,
            workstreams,
            subsystems,
            w3_rows,
            w3_evidence_html,
            inventory,
            _esc(projection["captured_at"]),
            _esc(projection["projection_schema"]),
        )
    )


def inject_personal_observatory(page: str, projection: Mapping[str, Any]) -> str:
    nav_marker = (
        '<a class="nav-item" data-target="trends"><span class="dot proposed"></span>'
        '<span class="lbl">🔭 路线与趋势</span></a>'
    )
    content_marker = '</main><aside class="toc" id="toc">'
    if nav_marker not in page:
        raise ValueError("Observatory navigation marker not found")
    if content_marker not in page:
        raise ValueError("Observatory content marker not found")
    if "</style>" not in page:
        raise ValueError("document style marker not found")
    active_css = ""
    active_js = ""
    if projection.get("contract_type") == "orrery-active-task-projection-v1":
        from .active_task_projection import ACTIVE_TASK_CSS, ACTIVE_TASK_JS

        active_css = ACTIVE_TASK_CSS
        active_js = ACTIVE_TASK_JS
    result = page.replace(
        "</style>", PERSONAL_OBSERVATORY_CSS + MAINTENANCE_OBSERVATORY_CSS + active_css + "</style>", 1
    )
    nav_item = (
        '<a class="nav-item" data-target="personal-observatory">'
        '<span class="dot state"></span><span class="lbl">个人工作台</span></a>'
    )
    maintenance_nav = (
        '<a class="nav-item" data-target="workspace-maintenance">'
        '<span class="dot state"></span><span class="lbl">工作区维护</span></a>'
    )
    result = result.replace(nav_marker, nav_marker + nav_item + maintenance_nav, 1)
    result = result.replace(
        content_marker,
        render_personal_observatory_panel(projection)
        + _maintenance_panel(projection)
        + content_marker,
        1,
    )
    return result.replace(
        "</body>", "<script>" + MAINTENANCE_OBSERVATORY_JS + active_js + "</script></body>", 1
    )


def write_projection_json(path: Path, projection: Mapping[str, Any]) -> None:
    """Write an explicitly requested disposable snapshot outside authority docs."""

    target = Path(os.path.abspath(os.fspath(path.expanduser())))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
