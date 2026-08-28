#!/usr/bin/env python3
"""Deterministic, credential-free W5D two-member acceptance runner.

All sockets bind loopback and discovery uses an injected in-memory transport.
Raw results are written to a new system-temporary directory, never the repo.
"""
from __future__ import annotations

import base64
import copy
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
for source in (
    REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src",
    REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src",
):
    sys.path.insert(0, str(source))

from project_orrery_core import __version__ as CORE_VERSION  # noqa: E402
from project_orrery_core.collaboration import compute_overlap_findings  # noqa: E402
from project_orrery_core.team import (  # noqa: E402
    _coordinator_path,
    _credential_path,
    _http_json,
    _json_bytes,
    _read_json,
    accept_envelope,
    aggregate_projection,
    build_discovery_packet,
    capture_metadata_envelope,
    change_member_capability,
    claim_coordinator_host_switch,
    confirm_join,
    create_coordinator_host_switch_invite,
    create_invite,
    decide_request,
    enable_team,
    fetch_projection,
    fetch_requests,
    finalize_join,
    project_fingerprint,
    publish_discovery_once,
    queue_sync_event,
    request_join,
    scan_discovery_candidates,
    send_request,
    start_coordinator_server,
    stop_owned_coordinator_server,
    sync_now,
    validate_discovery_packet,
)
from project_orrery_cli import __version__ as CLI_VERSION  # noqa: E402


SCHEMA = "project-orrery-lan-acceptance-v1"
FIXED_CLOCK = "2026-08-27T20:00:00Z"
FORBIDDEN_MANIFEST_TEXT = (
    "credential_token", "invite_secret", "switch_secret", "authorization", "source_code",
    "file_content", "prompt", "transcript", "api_key", "private_key",
)


class ControlledDiscoveryTransport:
    """A zero-socket broadcast bus used by CI and the single-machine Harness."""

    def __init__(self) -> None:
        self.packets: list[bytes] = []

    def send(self, payload: bytes, *, target: str, port: int) -> None:
        del target, port
        self.packets.append(bytes(payload))

    def receive(self, *, bind: str, port: int, timeout_seconds: float):
        del bind, port, timeout_seconds
        return [(packet, "controlled-loopback") for packet in self.packets]


def _run(*arguments: str, cwd: Path) -> str:
    environment = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "",
    }
    completed = subprocess.run(
        list(arguments), cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=environment, check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"local fixture command failed: {arguments[0]} {arguments[1]}")
    return completed.stdout.strip()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _future(minutes: int = 10) -> str:
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _start(root: Path):
    server, runtime = start_coordinator_server(root, bind="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    return server, runtime, thread


def _stop(root: Path, server: Any, thread: threading.Thread) -> None:
    stop_owned_coordinator_server(root, server)
    thread.join(timeout=5)
    if thread.is_alive():
        raise RuntimeError("loopback Coordinator did not stop")


def _make_clones(run_root: Path) -> tuple[Path, Path]:
    seed = run_root / "seed"
    seed.mkdir()
    _run("git", "init", "-b", "main", cwd=seed)
    _run("git", "config", "user.name", "Orrery Acceptance", cwd=seed)
    _run("git", "config", "user.email", "acceptance@example.invalid", cwd=seed)
    (seed / ".project-orrery.json").write_text(
        json.dumps({"manifest_format": 1, "name": "W5D isolated fixture"}, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    (seed / "local-work.txt").write_text("local work survives disconnect\n", encoding="utf-8", newline="\n")
    _run("git", "add", ".", cwd=seed)
    _run("git", "commit", "-m", "fixture", cwd=seed)
    host = run_root / "member-owner"
    member = run_root / "member-reviewer"
    _run("git", "clone", "--no-hardlinks", str(seed), str(host), cwd=run_root)
    _run("git", "clone", "--no-hardlinks", str(seed), str(member), cwd=run_root)
    _run("git", "config", "user.name", "Owner Device", cwd=host)
    _run("git", "config", "user.email", "owner@example.invalid", cwd=host)
    _run("git", "config", "user.name", "Reviewer Device", cwd=member)
    _run("git", "config", "user.email", "reviewer@example.invalid", cwd=member)
    return host, member


def _mutate_invite(encoded: str, **changes: Any) -> str:
    padding = "=" * (-len(encoded) % 4)
    value = json.loads(base64.urlsafe_b64decode(encoded + padding).decode("utf-8"))
    value.update(changes)
    return base64.urlsafe_b64encode(_json_bytes(value)).decode("ascii").rstrip("=")


def _lineage_scope(
    workstream_id: str, head: str, entries: list[tuple[str, str]],
    *, parent: str | None = None, task_base: str | None = None,
) -> dict[str, Any]:
    lineage = {
        "lineage_schema_version": 1,
        "status": "current" if parent else "legacy-unknown",
        "base_workstream_id": parent,
        "task_base_oid": task_base,
        "validated_head": head if parent else None,
    }
    path_entries = []
    for path, oid in entries:
        authority = [f"state:{path}"] if path.startswith("docs/state/") else []
        path_entries.append({
            "path": path, "is_pattern": False, "sources": ["committed"],
            "committed_last_oid": oid, "authority_surfaces": authority,
            "subsystem_ids": ["project-structure"], "exclusive_resource_ids": [],
        })
    return {
        "schema_version": 1, "contract_type": "scope-observation",
        "workstream_id": workstream_id, "worktree_id": f"fixture-{workstream_id}",
        "member_id": f"member-{workstream_id}", "host_id": f"host-{workstream_id}",
        "branch": f"refs/heads/{workstream_id}", "head": head,
        "integration_ref": "refs/heads/main", "integration_oid": "0" * 40,
        "merge_base": "0" * 40, "scope_revision": 1,
        "declared_subsystem_ids": ["project-structure"],
        "derived_subsystem_ids": ["project-structure"], "path_entries": path_entries,
        "governing_docs": [], "validation_surfaces": [],
        "scope_fingerprint": hashlib.sha256(workstream_id.encode("utf-8")).hexdigest(),
        "visibility": "worktree-local", "observability": "local",
        "captured_at": FIXED_CLOCK, "lineage": lineage,
    }


def _run_lineage_stage() -> dict[str, Any]:
    w5c_oid, w6_oid, w5d_oid, postfork_oid = (character * 40 for character in "1234")
    state_path = "docs/state/project-structure.md"
    w6_path = "chain/w6-only.txt"
    legacy = [
        _lineage_scope("W5C", w5c_oid, [(state_path, w5c_oid)]),
        _lineage_scope("W6", w6_oid, [(state_path, w5c_oid), (w6_path, w6_oid)]),
        _lineage_scope(
            "W5D", w5d_oid,
            [(state_path, w5c_oid), (w6_path, w5d_oid), ("chain/w5d-only.txt", w5d_oid)],
        ),
    ]
    before = compute_overlap_findings(legacy)
    stacked = [
        legacy[0],
        _lineage_scope("W6", w6_oid, [(w6_path, w6_oid)], parent="W5C", task_base=w5c_oid),
        _lineage_scope(
            "W5D", w5d_oid, [(w6_path, w5d_oid), ("chain/w5d-only.txt", w5d_oid)],
            parent="W6", task_base=w6_oid,
        ),
    ]
    proofs = {"W6": [w5c_oid], "W5D": [w5c_oid, w6_oid]}
    after = compute_overlap_findings(stacked, lineage_ancestry_proofs=proofs)
    before_counts = {
        kind: sum(item["kind"] == kind for item in before["findings"])
        for kind in ("direct", "authority")
    }
    after_counts = {
        kind: sum(item["kind"] == kind for item in after["findings"])
        for kind in ("direct", "authority")
    }
    postfork = copy.deepcopy(stacked)
    postfork[1] = _lineage_scope(
        "W6", postfork_oid, [(w6_path, postfork_oid)], parent="W5C", task_base=w5c_oid,
    )
    collided = compute_overlap_findings(postfork, lineage_ancestry_proofs=proofs)
    if before_counts["direct"] == 0 or before_counts["authority"] == 0:
        raise AssertionError("legacy lineage fixture did not reproduce duplicate findings")
    if after_counts != {"direct": 0, "authority": 0}:
        raise AssertionError("verified stacked inheritance remained in the conflict finding set")
    if not any(
        item["kind"] == "direct" and item["workstream_ids"] == ["W5D", "W6"]
        for item in collided["findings"]
    ):
        raise AssertionError("parent post-fork change did not re-form a conflict")
    return {
        "id": "stacked-lineage", "status": "passed",
        "evidence": {
            "before": before_counts, "after": after_counts,
            "postfork_parent_conflict": True, "branch_name_inference": False,
        },
    }


def run_acceptance(output_parent: Path | None = None) -> tuple[Path, dict[str, Any]]:
    parent = Path(output_parent) if output_parent else Path(tempfile.gettempdir())
    run_root = Path(tempfile.mkdtemp(prefix="project-orrery-w5d-acceptance-", dir=parent))
    stages: list[dict[str, Any]] = []
    owner_root = reviewer_root = None
    host_server = new_server = None
    host_thread = new_thread = None
    try:
        owner_root, reviewer_root = _make_clones(run_root)
        stages.append({"id": "isolated-clones", "status": "passed", "evidence": {"clone_count": 2, "shared_worktree": False}})
        stages.append(_run_lineage_stage())

        enable_team(owner_root, member_id="owner", device_id="device-a", host_id="host-a")
        enable_team(reviewer_root, member_id="reviewer", device_id="device-b", host_id="host-b")
        if project_fingerprint(owner_root) != project_fingerprint(reviewer_root):
            raise AssertionError("clone project fingerprints diverged")
        host_server, runtime, host_thread = _start(owner_root)

        bus = ControlledDiscoveryTransport()
        announced = publish_discovery_once(
            owner_root, endpoint=runtime["endpoint"], target="127.0.0.1", transport=bus,
        )
        leaked_keys = set(announced["packet"]) - {
            "schema_version", "contract_type", "protocol_version", "project_fingerprint",
            "host_hint", "device_hint", "endpoint", "nonce", "generated_at", "expires_at",
        }
        if leaked_keys:
            raise AssertionError("discovery packet leaked extra fields")
        bus.packets.append(bus.packets[0])
        scanned = scan_discovery_candidates(
            reviewer_root, bind="127.0.0.1", transport=bus,
        )
        if len(scanned["candidates"]) != 1 or scanned["rejected_count"] != 1:
            raise AssertionError("discovery replay was not rejected")
        candidate_id = scanned["candidates"][0]["candidate_id"]
        spoofed = copy.deepcopy(announced["packet"])
        spoofed["workstream"] = {"status": "forbidden"}
        try:
            validate_discovery_packet(spoofed)
        except ValueError:
            pass
        else:
            raise AssertionError("discovery schema accepted Team state")
        stages.append({
            "id": "discovery", "status": "passed",
            "evidence": {"candidate_count": 1, "replay_rejected": True, "membership_granted": False, "extra_fields": 0},
        })

        try:
            create_invite(
                owner_root, candidate_member_id="reviewer", endpoint=runtime["endpoint"],
                expires_at="2020-01-01T00:00:00Z",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("expired invite was accepted")
        invite = create_invite(
            owner_root, candidate_member_id="reviewer", endpoint=runtime["endpoint"], expires_at=_future()
        )
        cross_project = _mutate_invite(invite["invite"], project_fingerprint="0" * 64)
        try:
            request_join(reviewer_root, invite=cross_project, candidate_id=candidate_id)
        except ValueError:
            pass
        else:
            raise AssertionError("cross-project invitation was accepted")
        requested = request_join(reviewer_root, invite=invite["invite"], candidate_id=candidate_id)
        try:
            finalize_join(reviewer_root)
        except ValueError:
            pass
        else:
            raise AssertionError("unconfirmed member finalized join")
        try:
            request_join(reviewer_root, invite=invite["invite"], candidate_id=candidate_id)
        except ValueError:
            pass
        else:
            raise AssertionError("join invitation replay was accepted")
        confirm_join(owner_root, request_id=requested["request_id"])
        finalize_join(reviewer_root)
        stages.append({
            "id": "join", "status": "passed",
            "evidence": {"discovered_endpoint": True, "host_local_confirmation": True, "spoof_replay_cross_project_expiry_closed": True},
        })

        owner_envelope = capture_metadata_envelope(owner_root, occurred_at="2026-08-27T20:01:00Z")
        reviewer_envelope = capture_metadata_envelope(reviewer_root, occurred_at="2026-08-27T20:01:01Z")
        queue_sync_event(owner_root, owner_envelope, immediate=True)
        queue_sync_event(reviewer_root, reviewer_envelope, immediate=True)
        sync_now(owner_root, endpoint=runtime["endpoint"])
        sync_now(reviewer_root, endpoint=runtime["endpoint"])
        projection = fetch_projection(reviewer_root, endpoint=runtime["endpoint"])
        if [item["member_id"] for item in projection["members"]] != ["owner", "reviewer"]:
            raise AssertionError("two-member projection is incomplete")

        state = _read_json(_coordinator_path(owner_root))
        stale = aggregate_projection(state, now="2026-08-27T20:07:00Z")
        if {work["presence"] for member in stale["members"] for work in member["workstreams"]} != {"stale-unknown"}:
            raise AssertionError("TTL did not project stale-unknown")
        _stop(owner_root, host_server, host_thread)
        host_server = host_thread = None
        if (owner_root / "local-work.txt").read_text(encoding="utf-8") != "local work survives disconnect\n":
            raise AssertionError("disconnect changed local work")
        host_server, runtime, host_thread = _start(owner_root)
        fetch_projection(reviewer_root, endpoint=runtime["endpoint"])
        stages.append({
            "id": "sync-disconnect-reconnect", "status": "passed",
            "evidence": {"monotonic_revision": True, "ttl": "stale-unknown", "local_work_preserved": True, "reconnected": True},
        })

        request = send_request(
            reviewer_root, endpoint=runtime["endpoint"], target_member_id="owner",
            workstream_id=reviewer_envelope["workstream_id"], request_kind="pause-workstream",
            summary="Pause at the next local safe point",
        )
        inbox = fetch_requests(owner_root, endpoint=runtime["endpoint"])
        selected = next(item for item in inbox if item["request_id"] == request["request_id"])
        receipt = decide_request(
            owner_root, endpoint=runtime["endpoint"], request_record=selected,
            decision="accept", reason="Acceptance Harness local receipt only",
        )
        if receipt["execution_performed"] is not False:
            raise AssertionError("request-only boundary performed execution")

        switch = create_coordinator_host_switch_invite(
            owner_root, target_member_id="reviewer", target_host_id="host-b",
            target_device_id="device-b", endpoint=runtime["endpoint"], expires_at=_future(),
        )
        claimed = claim_coordinator_host_switch(reviewer_root, switch_invite=switch["switch_invite"])
        if claimed["coordinator_generation"] != 2:
            raise AssertionError("Coordinator generation did not advance")
        if '"secret"' in json.dumps(claimed, sort_keys=True):
            raise AssertionError("Host switch transferred ephemeral invitation authority")
        if any(
            item.get("status") in {"open", "pending-confirmation"}
            for item in claimed.get("invites", {}).values()
        ):
            raise AssertionError("Host switch preserved open join authority")
        try:
            fetch_projection(owner_root, endpoint=runtime["endpoint"])
        except ValueError:
            pass
        else:
            raise AssertionError("retired Coordinator accepted an operation")
        _stop(owner_root, host_server, host_thread)
        host_server = host_thread = None
        new_server, new_runtime, new_thread = _start(reviewer_root)
        reaggregated = fetch_projection(owner_root, endpoint=new_runtime["endpoint"])
        if reaggregated["coordinator"]["generation"] != 2:
            raise AssertionError("new Coordinator did not retain monotonic aggregate")
        duplicate = copy.deepcopy(reviewer_envelope)
        try:
            _http_json(
                new_runtime["endpoint"], "/v1/sync", method="POST", payload=duplicate,
                credential=_read_json(_credential_path(reviewer_root)),
            )
        except ValueError:
            pass
        else:
            raise AssertionError("older snapshot overwrote new Host state")
        stages.append({
            "id": "manual-host-switch", "status": "passed",
            "evidence": {
                "generation": 2, "old_host_retired": True, "automatic_election": False,
                "rollback_rejected": True, "ephemeral_authority_invalidated": True,
            },
        })

        old_credential = _read_json(_credential_path(reviewer_root))
        change_member_capability(
            reviewer_root, member_id="reviewer", action="grant", capability="reviewer", actor_id="owner"
        )
        change_member_capability(
            reviewer_root, member_id="reviewer", action="revoke", capability="reviewer", actor_id="owner"
        )
        try:
            _http_json(new_runtime["endpoint"], "/v1/projection", credential=old_credential)
        except ValueError:
            pass
        else:
            raise AssertionError("revoked capability credential remained usable")
        stages.append({
            "id": "request-and-revoke", "status": "passed",
            "evidence": {"request_only": True, "execution_performed": False, "old_credential_rejected": True},
        })

        _stop(reviewer_root, new_server, new_thread)
        new_server = new_thread = None
        stage_path = run_root / "stage-results.json"
        _write_json(stage_path, {"schema": SCHEMA, "stages": stages})
        manifest = {
            "schema": SCHEMA,
            "verdict": "passed",
            "parameters": {
                "members": 2, "transport": "controlled-discovery+loopback-http",
                "external_network": False, "real_credentials": False,
            },
            "runtime": {
                "python": platform.python_version(), "platform": platform.system().lower(),
                "core": CORE_VERSION, "cli": CLI_VERSION,
            },
            "artifacts": {"stage-results.json": _sha256(stage_path)},
            "stage_count": len(stages),
            "real_lan_validated": False,
        }
        manifest_path = run_root / "manifest.json"
        _write_json(manifest_path, manifest)
        verdict = {
            "schema": SCHEMA, "verdict": "passed",
            "manifest_sha256": _sha256(manifest_path), "stage_results_sha256": _sha256(stage_path),
        }
        _write_json(run_root / "verdict.json", verdict)
        validate_acceptance_run(run_root)
        return run_root, verdict
    except Exception:
        failure = {"schema": SCHEMA, "verdict": "failed", "failed_stage_index": len(stages)}
        _write_json(run_root / "verdict.json", failure)
        raise
    finally:
        if owner_root is not None and host_server is not None and host_thread is not None:
            try:
                _stop(owner_root, host_server, host_thread)
            except Exception:
                pass
        if reviewer_root is not None and new_server is not None and new_thread is not None:
            try:
                _stop(reviewer_root, new_server, new_thread)
            except Exception:
                pass


def validate_acceptance_run(run_root: Path) -> dict[str, Any]:
    root = Path(run_root)
    manifest_path = root / "manifest.json"
    stages_path = root / "stage-results.json"
    verdict_path = root / "verdict.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stages = json.loads(stages_path.read_text(encoding="utf-8"))
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA or verdict.get("schema") != SCHEMA:
        raise ValueError("acceptance schema mismatch")
    if manifest.get("verdict") != "passed" or verdict.get("verdict") != "passed":
        raise ValueError("acceptance verdict is not passed")
    if manifest.get("real_lan_validated") is not False:
        raise ValueError("single-machine Harness must not claim real LAN validation")
    if manifest.get("artifacts", {}).get("stage-results.json") != _sha256(stages_path):
        raise ValueError("stage-results checksum mismatch")
    if verdict.get("manifest_sha256") != _sha256(manifest_path):
        raise ValueError("manifest checksum mismatch")
    if verdict.get("stage_results_sha256") != _sha256(stages_path):
        raise ValueError("verdict stage checksum mismatch")
    if not stages.get("stages") or any(item.get("status") != "passed" for item in stages["stages"]):
        raise ValueError("one or more acceptance stages failed")
    serialized = json.dumps({"manifest": manifest, "stages": stages, "verdict": verdict}, sort_keys=True).lower()
    if any(fragment in serialized for fragment in FORBIDDEN_MANIFEST_TEXT):
        raise ValueError("acceptance artifacts contain a forbidden secret/content field")
    if str(root).lower() in serialized or str(REPOSITORY_ROOT).lower() in serialized:
        raise ValueError("acceptance artifacts contain an absolute local path")
    return {"schema": SCHEMA, "verdict": "passed", "validated_artifacts": 3}


def main() -> int:
    try:
        root, verdict = run_acceptance()
    except Exception as exc:
        print(json.dumps({"schema": SCHEMA, "verdict": "failed", "error_type": type(exc).__name__}))
        return 1
    print(json.dumps({**verdict, "raw_root": str(root)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
