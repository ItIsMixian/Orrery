from __future__ import annotations

import copy
import datetime as dt
import json
import socket
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
sys.path.insert(0, str(CORE_SOURCE))
sys.path.insert(0, str(CLI_SOURCE))
sys.path.insert(0, str(REPOSITORY_ROOT))

from project_orrery_core.team import (  # noqa: E402
    TEAM_CONTRACT_ID,
    TEAM_ENVELOPE_MAX_BYTES,
    _coordinator_path,
    _credential_path,
    _http_json,
    _read_json,
    accept_envelope,
    aggregate_projection,
    capture_metadata_envelope,
    change_member_capability,
    configure_heartbeat,
    confirm_join,
    create_invite,
    decide_request,
    disable_team,
    enable_team,
    fetch_projection,
    fetch_requests,
    finalize_join,
    inspect_outbox,
    load_team_config,
    project_fingerprint,
    queue_sync_event,
    request_host_switch,
    request_join,
    send_request,
    set_sharing,
    start_coordinator_server,
    switch_active_host,
    sync_now,
    team_private_dir,
    validate_metadata_envelope,
)
from project_orrery_cli import team as team_cli  # noqa: E402
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


TEAM_SCHEMA = CORE_SOURCE / "project_orrery_core" / "schema" / "team-v1.json"


class CoordinatorFixture:
    def __init__(self, root: Path):
        self.root = root
        self.server = None
        self.thread = None
        self.runtime = None

    def __enter__(self):
        self.server, self.runtime = start_coordinator_server(self.root, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05})
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.server is not None and self.thread is not None and self.thread.is_alive():
            self.server.shutdown()
        if self.server is not None:
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=3)


class TeamFoundationTests(unittest.TestCase):
    def _enable(self, root: Path, *, member: str = "owner", device: str = "device-a", host: str = "host-a"):
        return enable_team(root, member_id=member, device_id=device, host_id=host)

    def _queued_envelope(self, root: Path, *, occurred_at: str = "2026-08-23T01:00:00Z"):
        envelope = capture_metadata_envelope(root, occurred_at=occurred_at)
        queue_sync_event(root, envelope)
        return envelope

    def _join(self, host_root: Path, candidate_root: Path, endpoint: str) -> str:
        self._enable(candidate_root, member="reviewer", device="device-b", host="host-b")
        expires = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        invite = create_invite(
            host_root, candidate_member_id="reviewer", endpoint=endpoint, expires_at=expires,
        )
        self.assertEqual(invite["discovery"], "unsupported-next-phase")
        requested = request_join(candidate_root, invite=invite["invite"])
        self.assertEqual(requested["status"], "pending-host-confirmation")
        confirm_join(host_root, request_id=requested["request_id"])
        finalized = finalize_join(candidate_root)
        self.assertEqual(finalized["status"], "joined")
        return requested["request_id"]

    def test_team_schema_and_personal_default_are_zero_network(self) -> None:
        schema = json.loads(TEAM_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], TEAM_CONTRACT_ID)
        self.assertFalse(schema["x-orrery-boundaries"]["personal_default_listener"])
        self.assertFalse(schema["x-orrery-boundaries"]["remote_execution"])
        with CollaborationGitFixture() as fixture:
            with mock.patch.object(socket.socket, "bind", side_effect=AssertionError("listener attempted")):
                status = load_team_config(fixture.repository)
                self.assertFalse(status["enabled"])
                with self.assertRaisesRegex(ValueError, "explicitly enabled"):
                    start_coordinator_server(fixture.repository)

    def test_explicit_enable_loopback_runtime_and_disable_preserve_local_facts(self) -> None:
        with CollaborationGitFixture() as fixture:
            marker = fixture.repository / "local-work.txt"
            marker.write_text("preserve me", encoding="utf-8")
            enabled = self._enable(fixture.repository)
            self.assertFalse(enabled["network_performed"])
            self.assertEqual(load_team_config(fixture.repository)["network_features"], [])
            with self.assertRaisesRegex(ValueError, "LAN.*allow_lan_bind"):
                start_coordinator_server(fixture.repository, bind="0.0.0.0")
            with CoordinatorFixture(fixture.repository) as coordinator:
                self.assertTrue(coordinator.runtime["endpoint"].startswith("http://127.0.0.1:"))
                disabled = disable_team(fixture.repository)
                coordinator.thread.join(timeout=3)
                self.assertFalse(coordinator.thread.is_alive())
                self.assertTrue(disabled["runtime_stopped"])
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve me")
            self.assertFalse(load_team_config(fixture.repository)["enabled"])
            self.assertEqual(load_team_config(fixture.repository)["network_features"], [])
            self._enable(fixture.repository)
            with CoordinatorFixture(fixture.repository) as coordinator:
                with self.assertRaisesRegex(ValueError, "already registered"):
                    start_coordinator_server(fixture.repository, port=0)
                projection = fetch_projection(fixture.repository, endpoint=coordinator.runtime["endpoint"])
                self.assertEqual(projection["members"][0]["member_id"], "owner")

    def test_manual_invite_requires_project_identity_and_host_confirmation(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            self.assertEqual(project_fingerprint(fixture.repository), project_fingerprint(fixture.clone))
            with CoordinatorFixture(fixture.repository) as coordinator:
                self._enable(fixture.clone, member="reviewer", device="device-b", host="host-b")
                expires = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat().replace("+00:00", "Z")
                invite = create_invite(
                    fixture.repository, candidate_member_id="reviewer",
                    endpoint=coordinator.runtime["endpoint"], expires_at=expires,
                )
                requested = request_join(fixture.clone, invite=invite["invite"])
                with self.assertRaisesRegex(ValueError, "not Host-confirmed"):
                    finalize_join(fixture.clone)
                confirm_join(fixture.repository, request_id=requested["request_id"])
                finalize_join(fixture.clone)
                projection = fetch_projection(fixture.clone, endpoint=coordinator.runtime["endpoint"])
                self.assertEqual([member["member_id"] for member in projection["members"]], ["owner", "reviewer"])

    def test_nonmember_cannot_read_projection_or_publish_state(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            with CoordinatorFixture(fixture.repository) as coordinator:
                with self.assertRaisesRegex(ValueError, "membership credential required"):
                    _http_json(coordinator.runtime["endpoint"], "/v1/projection")
                envelope = capture_metadata_envelope(fixture.repository)
                fake = {"schema_version": 1, "member_id": "intruder", "credential_epoch": 1, "token": "not-valid"}
                with self.assertRaisesRegex(ValueError, "invalid project membership"):
                    _http_json(
                        coordinator.runtime["endpoint"], "/v1/sync", method="POST",
                        payload=envelope, credential=fake,
                    )

    def test_envelope_recursively_rejects_forbidden_fields_and_large_payloads(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            envelope = capture_metadata_envelope(fixture.repository)
            forbidden = copy.deepcopy(envelope)
            forbidden["scope"]["prompt"] = "do not sync"
            with self.assertRaisesRegex(ValueError, "forbidden Team payload field"):
                validate_metadata_envelope(forbidden)
            unknown = copy.deepcopy(envelope)
            unknown["arbitrary"] = {"file_content": "x"}
            with self.assertRaisesRegex(ValueError, "forbidden Team payload field"):
                validate_metadata_envelope(unknown)
            with self.assertRaisesRegex(ValueError, "64 KiB"):
                validate_metadata_envelope(envelope, raw_size=TEAM_ENVELOPE_MAX_BYTES + 1)
            malformed = copy.deepcopy(envelope)
            malformed["git"]["dirty_count"] = "zero"
            with self.assertRaisesRegex(ValueError, "dirty_count"):
                validate_metadata_envelope(malformed)

    def test_event_outbox_coalesces_and_immediate_sync_drains_it(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            first = capture_metadata_envelope(fixture.repository, occurred_at="2026-08-23T01:00:00Z")
            second = capture_metadata_envelope(fixture.repository, occurred_at="2026-08-23T01:00:01Z")
            queue_sync_event(fixture.repository, first)
            queued = queue_sync_event(fixture.repository, second, immediate=True)
            self.assertEqual(queued["event_count"], 1)
            self.assertEqual(inspect_outbox(fixture.repository)["events"][0]["envelope"]["revision"], second["revision"])
            with CoordinatorFixture(fixture.repository) as coordinator:
                synced = sync_now(fixture.repository, endpoint=coordinator.runtime["endpoint"])
                self.assertEqual(synced["accepted"], 1)
                self.assertEqual(inspect_outbox(fixture.repository)["events"], [])

    def test_monotonic_revision_rejects_rollback_and_duplicate(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            state = _read_json(_coordinator_path(fixture.repository))
            envelope = capture_metadata_envelope(fixture.repository)
            self.assertTrue(accept_envelope(state, envelope)["accepted"])
            with self.assertRaisesRegex(ValueError, "rollback or duplicate"):
                accept_envelope(state, envelope)
            older = copy.deepcopy(envelope)
            older["revision"] = 1
            with self.assertRaisesRegex(ValueError, "rollback or duplicate"):
                accept_envelope(state, older)

    def test_manual_active_host_switch_blocks_old_host_and_accepts_newer_revision(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            with CoordinatorFixture(fixture.repository) as coordinator:
                self._queued_envelope(fixture.repository)
                sync_now(fixture.repository, endpoint=coordinator.runtime["endpoint"])
                switch_active_host(fixture.repository, host_id="host-b", device_id="device-b")
                newer = capture_metadata_envelope(fixture.repository, occurred_at="2026-08-23T01:00:10Z")
                queue_sync_event(fixture.repository, newer)
                with self.assertRaisesRegex(ValueError, "manually selected active Host"):
                    sync_now(fixture.repository, endpoint=coordinator.runtime["endpoint"])
                request_host_switch(fixture.repository, endpoint=coordinator.runtime["endpoint"])
                synced = sync_now(fixture.repository, endpoint=coordinator.runtime["endpoint"])
                self.assertEqual(synced["accepted"], 1)
                projection = fetch_projection(fixture.repository, endpoint=coordinator.runtime["endpoint"])
                self.assertEqual(projection["members"][0]["active_host"]["host_id"], "host-b")

    def test_heartbeat_is_off_by_default_and_ttl_never_presents_snapshot_as_live(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            envelope = capture_metadata_envelope(fixture.repository, occurred_at="2026-08-23T01:00:00Z")
            state = _read_json(_coordinator_path(fixture.repository))
            accept_envelope(state, envelope)
            fresh = aggregate_projection(state, now="2026-08-23T01:00:01Z")
            self.assertEqual(fresh["members"][0]["workstreams"][0]["presence"], "unknown")
            stale = aggregate_projection(state, now="2026-08-23T01:06:00Z")
            self.assertEqual(stale["members"][0]["workstreams"][0]["presence"], "stale-unknown")
            configure_heartbeat(fixture.repository, enabled=True, interval_seconds=30)
            heartbeat = capture_metadata_envelope(fixture.repository, occurred_at="2026-08-23T02:00:00Z")
            accept_envelope(state, heartbeat)
            online = aggregate_projection(state, now="2026-08-23T02:00:40Z")
            self.assertEqual(online["members"][0]["workstreams"][0]["presence"], "online")
            configure_heartbeat(fixture.repository, enabled=False, interval_seconds=30)
            self.assertFalse(load_team_config(fixture.repository)["heartbeat"]["enabled"])

    def test_central_requests_require_local_receipt_and_never_execute(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            with CoordinatorFixture(fixture.repository) as coordinator:
                created = send_request(
                    fixture.repository, endpoint=coordinator.runtime["endpoint"],
                    target_member_id="owner", workstream_id="W5-local", request_kind="pause-workstream",
                    summary="Please pause after the current safe point",
                )
                self.assertFalse(created["execution_performed"])
                inbox = fetch_requests(fixture.repository, endpoint=coordinator.runtime["endpoint"])
                decided = decide_request(
                    fixture.repository, endpoint=coordinator.runtime["endpoint"],
                    request_record=inbox[0], decision="accept", reason="Recorded locally; no action executed",
                )
                self.assertEqual(decided["status"], "accepted-locally")
                self.assertFalse(decided["execution_performed"])
                receipt = team_private_dir(fixture.repository) / "inbox" / f"{created['request_id']}.json"
                self.assertTrue(receipt.exists())
                self.assertFalse(json.loads(receipt.read_text(encoding="utf-8"))["execution_performed"])

    def test_capability_revoke_invalidates_old_member_credential(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            with CoordinatorFixture(fixture.repository) as coordinator:
                self._join(fixture.repository, fixture.clone, coordinator.runtime["endpoint"])
                old_credential = _read_json(_credential_path(fixture.clone))
                change_member_capability(
                    fixture.repository, member_id="reviewer", action="grant", capability="reviewer",
                )
                changed = change_member_capability(
                    fixture.repository, member_id="reviewer", action="revoke", capability="reviewer",
                )
                self.assertTrue(changed["old_credentials_revoked"])
                with self.assertRaisesRegex(ValueError, "revoked or stale"):
                    _http_json(
                        coordinator.runtime["endpoint"], "/v1/projection", credential=old_credential,
                    )

    def test_public_or_dns_endpoints_are_rejected_before_network_and_cli_is_stable(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            with mock.patch("project_orrery_core.team.urlopen", side_effect=AssertionError("external network attempted")):
                with self.assertRaisesRegex(ValueError, "IP literal"):
                    fetch_projection(fixture.repository, endpoint="http://example.com:80")
                with self.assertRaisesRegex(ValueError, "private IP"):
                    fetch_projection(fixture.repository, endpoint="http://8.8.8.8:80")
            self.assertEqual(team_cli.main(["status", "--target", str(fixture.repository), "--json"]), 0)
            self.assertEqual(
                team_cli.main([
                    "heartbeat", "off", "--target", str(fixture.repository),
                    "--interval-seconds", "30", "--json",
                ]),
                0,
            )

    def test_sharing_off_projects_unavailable_without_deleting_local_state(self) -> None:
        with CollaborationGitFixture() as fixture:
            self._enable(fixture.repository)
            set_sharing(fixture.repository, enabled=False)
            envelope = capture_metadata_envelope(fixture.repository, occurred_at="2026-08-23T01:00:00Z")
            state = _read_json(_coordinator_path(fixture.repository))
            accept_envelope(state, envelope)
            projection = aggregate_projection(state, now="2026-08-23T01:00:01Z")
            self.assertEqual(projection["members"][0]["workstreams"][0]["presence"], "unavailable")
            self.assertTrue(_coordinator_path(fixture.repository).exists())


if __name__ == "__main__":
    unittest.main()
